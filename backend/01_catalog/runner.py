"""
Node runner — `run_node(pool, key, ctx, inputs) -> dict` (NCP v1 §7, §8, §9).

The ONLY sanctioned mechanism for a sub-feature to invoke behavior in
another sub-feature. Enforces execution policy (timeout, retries on
TransientError, tx modes) and runs the authz hook before dispatch.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from importlib import import_module as _import_module
from typing import Any

import asyncpg
from pydantic import BaseModel, ValidationError

_context: Any = _import_module("backend.01_catalog.context")
_errors: Any = _import_module("backend.01_catalog.errors")
_authz: Any = _import_module("backend.01_catalog.authz")
_manifest_mod: Any = _import_module("backend.01_catalog.manifest")
_loader: Any = _import_module("backend.01_catalog.loader")

logger = logging.getLogger("tennetctl.runner")

_SCHEMA = '"01_catalog"'

# Handler cache: node_key → handler class. Populated on first resolution.
# Hot-reload (backend/01_catalog/hot_reload.py) calls `invalidate_handlers()`
# when a manifest changes in dev mode, ensuring code edits are picked up
# without a backend restart.
_HANDLER_CACHE: dict[str, type] = {}


def invalidate_handlers(key: str | None = None) -> None:
    """Evict cached handler classes.

    Called by the hot-reload watcher in dev, and by tests that need to
    re-import handler modules. Safe to call at any time — next `run_node`
    resolution will re-walk the manifest and populate the cache.
    """
    if key is None:
        _HANDLER_CACHE.clear()
    else:
        _HANDLER_CACHE.pop(key, None)


async def _lookup_node(conn: Any, key: str) -> dict | None:
    """Fetch node metadata joined with kind + tx mode codes. Returns dict or None."""
    row = await conn.fetchrow(
        f"""
        SELECT n.id, n.key, n.handler_path, n.version, n.emits_audit,
               n.timeout_ms, n.retries, n.deprecated_at, n.tombstoned_at,
               k.code AS kind_code, t.code AS tx_mode_code
        FROM {_SCHEMA}."12_fct_nodes" n
          JOIN {_SCHEMA}."02_dim_node_kinds" k ON k.id = n.kind_id
          JOIN {_SCHEMA}."03_dim_tx_modes" t ON t.id = n.tx_mode_id
        WHERE n.key = $1
        """,
        key,
    )
    if row is None:
        return None
    return dict(row)


def _resolve_handler(meta: dict) -> type:
    """
    Use the loader's shared handler path resolution logic by walking manifests.
    Fast path: the catalog row has the relative handler_path; we need the feature
    directory too. Search both real + fixture manifests for a match on the key.

    Cached after first resolution — the manifest walk is O(features) and
    importlib has its own module cache, but skipping both on hot paths is worth
    a dict lookup. See `invalidate_handlers()` for the hot-reload hook.
    """
    key = meta["key"]
    cached = _HANDLER_CACHE.get(key)
    if cached is not None:
        return cached
    # Find the feature this node belongs to. We know key format is
    # "{feature}.{sub}.{action..}", so feature_key is the first segment.
    feature_key = key.split(".", 1)[0]

    # Walk all known manifest paths (real + fixtures) until we find one whose
    # metadata.key matches. This is O(features) per run_node call; catalog boot
    # amortizes this but runner must also resolve at call time for dynamic dispatch.
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    candidates = _manifest_mod.discover_manifests(root, include_fixtures=True)
    for manifest_path in candidates:
        try:
            fm = _manifest_mod.parse_manifest(manifest_path)
        except _errors.RunnerError:
            continue
        except Exception:
            continue
        if fm.metadata.key != feature_key:
            continue
        # Convert handler path using loader's helper
        module_path = _loader._handler_import_path(manifest_path, meta["handler_path"])
        attr = meta["handler_path"].rsplit(".", 1)[-1]
        mod = _import_module(module_path)
        handler_cls = getattr(mod, attr)
        _HANDLER_CACHE[key] = handler_cls
        return handler_cls
    raise _errors.NodeNotFound(
        f"handler for node {key!r} could not be resolved (no matching manifest found)",
        node_key=key,
    )


def _is_transient(exc: BaseException) -> bool:
    """Return True iff the exception is retryable per NCP §8."""
    return isinstance(exc, _errors.TransientError)


async def _invoke_once(
    handler: Any,
    ctx: Any,
    validated_input: BaseModel,
    effective_timeout_ms: int,
) -> Any:
    """Run one attempt of the handler under a timeout. Raises NodeTimeout on expiry."""
    try:
        return await asyncio.wait_for(
            handler.run(ctx, validated_input),
            timeout=effective_timeout_ms / 1000.0,
        )
    except asyncio.TimeoutError as e:
        raise _errors.NodeTimeout(
            f"node exceeded timeout_ms={effective_timeout_ms}",
            node_key=getattr(handler, "key", None),
        ) from e


async def _validate_output(handler_cls: type, result: Any) -> dict:
    """Coerce + validate handler output against Output class. Returns dict."""
    output_cls = handler_cls.Output  # type: ignore[attr-defined]
    if isinstance(result, output_cls):
        return result.model_dump()
    if isinstance(result, BaseModel):
        # Wrong Output class — try dumping and revalidating
        return output_cls(**result.model_dump()).model_dump()
    if isinstance(result, dict):
        return output_cls(**result).model_dump()
    raise _errors.DomainError(
        f"handler returned {type(result).__name__}, expected dict or {output_cls.__name__}",
        node_key=getattr(handler_cls, "key", None),
    )


async def run_node(
    pool: asyncpg.Pool,
    key: str,
    ctx: Any = None,
    inputs: dict | None = None,
) -> dict:
    """
    Dispatch a node call through the catalog.

    - Looks up `key` in fct_nodes (joined with dim_node_kinds + dim_tx_modes)
    - Runs authorization hook
    - Resolves handler via importlib from the manifest
    - Validates inputs via handler.Input
    - Applies tx mode (none/caller/own) and timeout
    - Retries on TransientError only (if retries>0 and idempotency_key provided)
    - Validates output via handler.Output
    - Returns validated dict
    """
    if ctx is None:
        ctx = _context.NodeContext.system()
    if inputs is None:
        inputs = {}

    # 1. Lookup
    async with pool.acquire() as probe_conn:
        meta = await _lookup_node(probe_conn, key)
    if meta is None:
        raise _errors.NodeNotFound(f"no catalog entry for key {key!r}", node_key=key)
    if meta["tombstoned_at"] is not None:
        raise _errors.NodeTombstoned(f"node {key!r} is tombstoned", node_key=key)
    if meta["deprecated_at"] is not None:
        logger.warning("Calling deprecated node %r", key)

    # 2. Runtime defense-in-depth: effect nodes must emit audit
    if meta["kind_code"] == "effect" and not meta["emits_audit"]:
        raise _errors.DomainError(
            "effect node must have emits_audit=true (runtime safety net; DB CHECK should have prevented this)",
            node_key=key,
        )

    # 3. Authz
    await _authz.check_call(ctx, meta)

    # 4. Resolve handler
    try:
        handler_cls = _resolve_handler(meta)
    except _errors.RunnerError:
        raise
    except Exception as e:
        raise _errors.NodeNotFound(
            f"handler resolution failed: {e}", node_key=key,
        ) from e
    handler = handler_cls()

    # 5. Idempotency check — if retries configured, caller must provide key.
    # Runs BEFORE input validation so a missing key is diagnosed precisely
    # (not hidden behind a Pydantic "field required" error).
    retries = int(meta["retries"] or 0)
    if retries > 0 and "idempotency_key" not in inputs:
        raise _errors.IdempotencyRequired(
            f"node {key!r} has retries={retries}; caller must provide idempotency_key in inputs",
            node_key=key,
        )

    # 6. Validate inputs
    try:
        validated_input = handler_cls.Input(**inputs)  # type: ignore[attr-defined]
    except ValidationError as e:
        raise _errors.DomainError(
            f"input validation failed: {e}", node_key=key,
        ) from e

    # 7. Child context for trace tree
    child_ctx = ctx.child_span(key)

    # 8. Effective timeout
    effective_ms = (
        ctx.timeout_override_ms
        if ctx.timeout_override_ms is not None
        else int(meta["timeout_ms"])
    )

    # 9. Transaction mode + handler invocation with retry loop
    tx_mode = meta["tx_mode_code"]
    max_attempts = retries + 1
    last_exc: BaseException | None = None

    async def _run_with_conn(conn: Any) -> dict:
        nonlocal last_exc
        attempt_ctx = replace(child_ctx, conn=conn) if conn is not None else child_ctx
        for attempt in range(1, max_attempts + 1):
            try:
                result = await _invoke_once(handler, attempt_ctx, validated_input, effective_ms)
                return await _validate_output(handler_cls, result)
            except BaseException as exc:
                last_exc = exc
                if attempt < max_attempts and _is_transient(exc):
                    logger.info(
                        "Retrying node %r attempt %d/%d after transient: %s",
                        key, attempt, max_attempts, exc,
                    )
                    await asyncio.sleep(0.05 * attempt)
                    continue
                raise
        # Should not reach here; satisfy type checker
        raise last_exc if last_exc else _errors.RunnerError(f"unknown error in {key!r}", node_key=key)

    if tx_mode == "none":
        return await _run_with_conn(None)

    if tx_mode == "own":
        async with pool.acquire() as conn:
            async with conn.transaction():
                return await _run_with_conn(conn)

    # "caller": reuse ctx.conn if set, else acquire and pass (no new tx)
    if ctx.conn is not None:
        return await _run_with_conn(ctx.conn)
    async with pool.acquire() as conn:
        return await _run_with_conn(conn)

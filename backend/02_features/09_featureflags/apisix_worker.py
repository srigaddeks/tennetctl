"""
featureflags.apisix_worker — background poll loop publishing request-path
flags to APISIX.

Runs every `poll_seconds` (default 30s). Each cycle:

  1. Acquires a pool connection.
  2. Calls `apisix_writer.publish()`.
  3. Emits `flags.apisix.synced` audit if the content changed (or first success).
  4. Emits `flags.apisix.sync_failed` audit on error-state transitions.
  5. Stores the last PublishResult on `app.state.apisix_sync_status` so the
     admin UI + a status endpoint can render it.

The worker is gated on `featureflags` being an active module and the pool
being ready; otherwise it exits cleanly.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict
from importlib import import_module
from typing import Any

from . import apisix_writer

logger = logging.getLogger("tennetctl.featureflags.apisix_worker")

DEFAULT_POLL_SECONDS = 30.0


async def _emit_audit(
    pool: Any,
    *,
    event_key: str,
    outcome: str,
    metadata: dict,
) -> None:
    """Fire-and-forget audit emit. Uses a fresh conn so we never block the worker."""
    try:
        _catalog = import_module("backend.01_catalog")
        _catalog_ctx = import_module("backend.01_catalog.context")
        _core_id = import_module("backend.01_core.id")

        ctx = _catalog_ctx.NodeContext(
            user_id=None,
            session_id=None,
            org_id=None,
            workspace_id=None,
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(),
            audit_category="system",  # bypasses audit-scope requirement
            pool=pool,
            extras={"pool": pool},
        )
        await _catalog.run_node(
            pool,
            "audit.events.emit",
            ctx,
            {
                "category": "system",
                "event_key": event_key,
                "outcome": outcome,
                "metadata": metadata,
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("apisix audit emit failed (%s): %s", event_key, exc)


async def publish_once(pool: Any) -> apisix_writer.PublishResult:
    """One-shot publish — useful for boot reconcile + tests."""
    async with pool.acquire() as conn:
        return await apisix_writer.publish(conn)


async def run_worker(
    pool: Any,
    *,
    poll_seconds: float = DEFAULT_POLL_SECONDS,
    status_holder: dict | None = None,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Main worker loop.

    `status_holder` is a dict passed by the caller (typically `app.state.__dict__`
    but kept as a parameter to ease testing). On each successful publish the
    worker overwrites `status_holder["apisix_sync_status"]` with the latest
    PublishResult dict.
    """
    last_digest: str | None = None
    last_error: str | None = None

    logger.info(
        "apisix sync worker started (poll=%.1fs, path=%s)",
        poll_seconds, apisix_writer.ApisixWriterConfig.from_env().yaml_path,
    )

    # Immediate boot-reconcile so APISIX gets current state without waiting
    await _cycle(pool, status_holder, last_digest, last_error)

    while True:
        if stop_event is not None and stop_event.is_set():
            return
        try:
            await asyncio.sleep(poll_seconds)
        except asyncio.CancelledError:
            return

        last_digest, last_error = await _cycle(
            pool, status_holder, last_digest, last_error,
        )


async def _cycle(
    pool: Any,
    status_holder: dict | None,
    last_digest: str | None,
    last_error: str | None,
) -> tuple[str | None, str | None]:
    result = await publish_once(pool)

    if status_holder is not None:
        status_holder["apisix_sync_status"] = asdict(result)

    # Error-state-transition audit
    if result.error:
        if last_error != result.error:
            await _emit_audit(
                pool,
                event_key="flags.apisix.sync_failed",
                outcome="failure",
                metadata={
                    "error": result.error,
                    "configs_compiled": result.configs_compiled,
                },
            )
        return last_digest, result.error

    # Success + content change → emit audit
    if result.content_digest and (result.content_digest != last_digest):
        await _emit_audit(
            pool,
            event_key="flags.apisix.synced",
            outcome="success",
            metadata={
                "configs_compiled": result.configs_compiled,
                "yaml_written": result.yaml_written,
                "yaml_path": result.yaml_path,
                "admin_succeeded": result.admin_succeeded,
                "admin_failed": result.admin_failed,
                "digest": result.content_digest[:16],
            },
        )

    return result.content_digest, None


def start_task(pool: Any, *, status_holder: dict | None = None) -> asyncio.Task:
    """Convenience: spawn the worker as a background task."""
    return asyncio.create_task(run_worker(pool, status_holder=status_holder))


__all__ = ["run_worker", "publish_once", "start_task", "DEFAULT_POLL_SECONDS"]

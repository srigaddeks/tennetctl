"""
Boot loader — executes NCP v1 §11 sequence:
  discover → parse → filter by TENNETCTL_MODULES → resolve handlers →
  topsort → upsert (one tx per feature) → deprecation sweep.

Strict mode in v1: first error fails the whole boot after all errors are logged.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from importlib import import_module as _import_module
from pathlib import Path
from typing import Any

import asyncpg

# Numeric-prefix dirs require importlib; type checker can't follow, so we type as Any.
_manifest_mod: Any = _import_module("backend.01_catalog.manifest")
_repo: Any = _import_module("backend.01_catalog.repository")

logger = logging.getLogger("tennetctl.catalog")


@dataclass
class LoaderReport:
    features_upserted: int = 0
    sub_features_upserted: int = 0
    nodes_upserted: int = 0
    deprecated: int = 0
    errors: list[tuple[str, str, str]] = field(default_factory=list)  # (path, code, msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def _project_root() -> Path:
    # backend/01_catalog/loader.py → project root is 2 levels up
    return Path(__file__).resolve().parents[2]


def _handler_import_path(manifest_path: Path, handler_relative: str) -> str:
    """
    Map a node's handler path (relative inside the feature) to a fully qualified Python import path.

    Real feature:    backend/02_features/{nn}_{feature_key}/{handler_relative}
    Fixture feature: tests/fixtures/features/{nn}_{feature_key}/{handler_relative}
    """
    parts = manifest_path.parts
    # Identify whether this is a real feature or a fixture.
    try:
        i = parts.index("02_features")
        pkg_root = ".".join(parts[i - 1 : i + 2])  # backend.02_features.{nn}_{key}
    except ValueError:
        # Must be a fixture
        try:
            i = parts.index("features")
            # tests/fixtures/features/{nn}_{key}
            pkg_root = ".".join(parts[i - 2 : i + 2])  # tests.fixtures.features.{nn}_{key}
        except ValueError as exc:
            raise _manifest_mod.HandlerUnresolved(
                f"Cannot locate feature package root for manifest {manifest_path}"
            ) from exc
    return f"{pkg_root}.{handler_relative.rsplit('.', 1)[0]}"


def _resolve_handler(
    manifest_path: Path,
    handler_attr: str,
) -> object:
    """
    Import the module containing the handler and return the handler class (or raise).
    handler_attr format: 'sub_features.01_sample.nodes.ping_mod.PingNode'
    """
    module_path = _handler_import_path(manifest_path, handler_attr)
    attr = handler_attr.rsplit(".", 1)[-1]
    try:
        mod = _import_module(module_path)
    except ImportError as e:
        raise _manifest_mod.HandlerUnresolved(
            f"Cannot import handler module {module_path!r}: {e}", path=str(manifest_path),
        ) from e
    if not hasattr(mod, attr):
        raise _manifest_mod.HandlerUnresolved(
            f"Module {module_path!r} has no attribute {attr!r}", path=str(manifest_path),
        )
    return getattr(mod, attr)


def _verify_contract(
    handler_cls: object,
    node_key: str,
    node_kind: str,
    manifest_path: Path,
) -> None:
    """Handler class must expose `key` and `kind` attributes matching the manifest."""
    handler_key = getattr(handler_cls, "key", None)
    handler_kind = getattr(handler_cls, "kind", None)
    if handler_key != node_key:
        raise _manifest_mod.HandlerContractMismatch(
            f"Handler {handler_cls!r} has key={handler_key!r} but manifest declares {node_key!r}",
            path=str(manifest_path),
        )
    if handler_kind != node_kind:
        raise _manifest_mod.HandlerContractMismatch(
            f"Handler {handler_cls!r} has kind={handler_kind!r} but manifest declares {node_kind!r}",
            path=str(manifest_path),
        )


def _topsort(
    features: list[tuple[Path, Any]],
) -> list[tuple[Path, Any]]:
    """Kahn's algorithm over depends_on_modules. Cycle → CatalogError."""
    by_mod: dict[str, tuple[Path, Any]] = {fm.metadata.module: (p, fm) for p, fm in features}
    indeg: dict[str, int] = {mod: 0 for mod in by_mod}
    edges: dict[str, list[str]] = defaultdict(list)
    for _p, fm in features:
        for dep in fm.spec.depends_on_modules:
            if dep in by_mod:
                edges[dep].append(fm.metadata.module)
                indeg[fm.metadata.module] += 1
    queue = deque([m for m, d in indeg.items() if d == 0])
    ordered: list[tuple[Path, Any]] = []
    while queue:
        m = queue.popleft()
        ordered.append(by_mod[m])
        for nxt in edges[m]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
    if len(ordered) != len(features):
        raise _manifest_mod.CatalogError(
            "Dependency cycle among feature modules: "
            + ", ".join(sorted(m for m, d in indeg.items() if d > 0)),
        )
    return ordered


async def upsert_all(
    pool: asyncpg.Pool,
    enabled_modules: frozenset[str],
    *,
    fixtures: bool = False,
) -> LoaderReport:
    """Run the full NCP §11 boot sequence. Strict mode."""
    report = LoaderReport()
    root = _project_root()

    # 1. Discover
    manifest_paths = _manifest_mod.discover_manifests(root, include_fixtures=fixtures)
    logger.info("Discovered %d manifest(s)", len(manifest_paths))

    # 2. Parse
    parsed: list[tuple[Path, Any]] = []
    for p in manifest_paths:
        try:
            fm = _manifest_mod.parse_manifest(p)
        except _manifest_mod.ManifestInvalid as e:
            logger.error("Manifest invalid: %s", e)
            report.errors.append((str(p), e.code, str(e)))
            continue
        parsed.append((p, fm))

    # 3. Filter by enabled_modules
    filtered: list[tuple[Path, Any]] = []
    for p, fm in parsed:
        if fm.metadata.always_on or fm.metadata.module in enabled_modules:
            filtered.append((p, fm))
        else:
            logger.info(
                "Skipping feature %r (module %r not in TENNETCTL_MODULES)",
                fm.metadata.key, fm.metadata.module,
            )

    # 4. Resolve handlers
    for p, fm in filtered:
        for sub in fm.spec.sub_features:
            for node in sub.nodes:
                try:
                    handler_cls = _resolve_handler(p, node.handler)
                    _verify_contract(handler_cls, node.key, node.kind, p)
                except _manifest_mod.CatalogError as e:
                    logger.error("Handler resolution failed: %s", e)
                    report.errors.append((str(p), e.code, str(e)))

    # If any errors so far, fail fast BEFORE touching the DB.
    if report.errors:
        raise _manifest_mod.CatalogError(
            f"Manifest/handler validation failed with {len(report.errors)} error(s); "
            f"first: [{report.errors[0][1]}] {report.errors[0][2]}"
        )

    # 5. Topsort by depends_on_modules
    ordered = _topsort(filtered)

    # 6. Upsert (one tx per feature)
    feature_keys_seen: set[str] = set()
    sub_feature_keys_seen: set[str] = set()
    node_keys_seen: set[str] = set()

    for p, fm in ordered:
        feature_keys_seen.add(fm.metadata.key)
        async with pool.acquire() as conn:
            async with conn.transaction():
                module_id = await _repo.get_module_id(conn, fm.metadata.module)
                feature_id = await _repo.upsert_feature(
                    conn,
                    key=fm.metadata.key,
                    number=fm.metadata.number,
                    module_id=module_id,
                )
                report.features_upserted += 1
                for sub in fm.spec.sub_features:
                    sub_feature_keys_seen.add(sub.key)
                    sub_id = await _repo.upsert_sub_feature(
                        conn,
                        key=sub.key,
                        feature_id=feature_id,
                        number=sub.number,
                    )
                    report.sub_features_upserted += 1
                    for node in sub.nodes:
                        node_keys_seen.add(node.key)
                        kind_id = await _repo.get_node_kind_id(conn, node.kind)
                        tx_mode_id = await _repo.get_tx_mode_id(conn, node.execution.tx)
                        await _repo.upsert_node(
                            conn,
                            key=node.key,
                            sub_feature_id=sub_id,
                            kind_id=kind_id,
                            handler_path=node.handler,
                            version=node.version,
                            emits_audit=node.emits_audit,
                            timeout_ms=node.execution.timeout_ms,
                            retries=node.execution.retries,
                            tx_mode_id=tx_mode_id,
                        )
                        report.nodes_upserted += 1

    # 7. Deprecation sweep — any catalog row whose key wasn't observed this boot → deprecated_at=NOW()
    async with pool.acquire() as conn:
        report.deprecated += await _repo.mark_absent_deprecated(
            conn, table="12_fct_nodes", keys_present=node_keys_seen,
        )
        report.deprecated += await _repo.mark_absent_deprecated(
            conn, table="11_fct_sub_features", keys_present=sub_feature_keys_seen,
        )
        report.deprecated += await _repo.mark_absent_deprecated(
            conn, table="10_fct_features", keys_present=feature_keys_seen,
        )

    logger.info(
        "Catalog boot done: %d features, %d sub-features, %d nodes, %d deprecated",
        report.features_upserted,
        report.sub_features_upserted,
        report.nodes_upserted,
        report.deprecated,
    )
    return report

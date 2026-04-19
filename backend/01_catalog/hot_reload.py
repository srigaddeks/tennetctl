"""
Dev hot-reload: watch feature manifest files and invalidate catalog caches
when they change.

Opt-in via `DEBUG=true` — the watcher runs in a background asyncio task
spawned from the FastAPI lifespan. Polling-based to avoid pulling in a
watchdog dependency; polling interval defaults to 1 second.

On manifest change (mtime bump) the watcher:

  1. Invalidates the runner handler cache (future `run_node` calls pick
     up edited handler code).
  2. Re-runs the catalog loader against the project root (upserts any
     new/changed node metadata into Postgres).

Errors during reload are logged and swallowed — a broken manifest in dev
should not take down the backend.
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import sys
from dataclasses import dataclass, field
from importlib import import_module as _import_module
from pathlib import Path
from typing import Any

_runner: Any = _import_module("backend.01_catalog.runner")
_loader: Any = _import_module("backend.01_catalog.loader")
_manifest_mod: Any = _import_module("backend.01_catalog.manifest")

logger = logging.getLogger("tennetctl.catalog.hot_reload")

DEFAULT_POLL_SECONDS = 1.0


@dataclass
class _WatchState:
    mtimes: dict[Path, float] = field(default_factory=dict)


def _manifest_paths(project_root: Path) -> list[Path]:
    """Discover all feature manifests that ship with the running backend."""
    return list(_manifest_mod.discover_manifests(project_root, include_fixtures=False))


def _snapshot(paths: list[Path]) -> dict[Path, float]:
    """Return {path → mtime} for each manifest that still exists."""
    out: dict[Path, float] = {}
    for p in paths:
        try:
            out[p] = p.stat().st_mtime
        except FileNotFoundError:
            continue
    return out


def _reimport_handlers_for(paths: list[Path]) -> None:
    """Re-import handler modules referenced by changed manifests.

    importlib caches module objects in `sys.modules`; without `reload` the
    edited source would be ignored. We re-import each manifest's entire
    handler tree conservatively. Non-catastrophic: on error, log + continue.
    """
    for manifest_path in paths:
        try:
            fm = _manifest_mod.parse_manifest(manifest_path)
        except Exception as exc:  # noqa: BLE001 — dev tool, swallow + log
            logger.warning("hot-reload parse failed for %s: %s", manifest_path, exc)
            continue

        # Collect node handler module paths
        seen: set[str] = set()
        for sub in getattr(fm, "sub_features", []) or []:
            for node in getattr(sub, "nodes", []) or []:
                handler_attr = getattr(node, "handler_path", None)
                if not handler_attr:
                    continue
                try:
                    module_path = _loader._handler_import_path(manifest_path, handler_attr)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("hot-reload import-path failed: %s", exc)
                    continue
                if module_path in seen:
                    continue
                seen.add(module_path)

                existing = sys.modules.get(module_path)
                try:
                    if existing is not None:
                        importlib.reload(existing)
                    else:
                        _import_module(module_path)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("hot-reload reimport failed for %s: %s", module_path, exc)


async def _reload_cycle(pool: Any, project_root: Path, changed: list[Path]) -> None:
    """Invalidate runner cache, re-import handler modules, re-run catalog boot."""
    logger.info("hot-reload triggered by %d manifest change(s)", len(changed))
    _runner.invalidate_handlers()
    _reimport_handlers_for(changed)
    try:
        # Loader expects an async entrypoint; re-run the boot upsert
        if hasattr(_loader, "boot_load"):
            await _loader.boot_load(pool, project_root)
        elif hasattr(_loader, "load_all"):
            await _loader.load_all(pool, project_root)
    except Exception as exc:  # noqa: BLE001
        logger.warning("hot-reload catalog refresh failed: %s", exc)


async def watch_manifests(
    pool: Any,
    *,
    project_root: Path | None = None,
    poll_seconds: float = DEFAULT_POLL_SECONDS,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Background task — watch manifest mtimes and hot-reload on change.

    Intended to be started once from FastAPI lifespan and cancelled on
    shutdown. `stop_event` is optional; cancellation via task cancel also
    works.
    """
    if project_root is None:
        project_root = Path(__file__).resolve().parents[2]

    state = _WatchState(mtimes=_snapshot(_manifest_paths(project_root)))
    logger.info("catalog hot-reload watching %d manifests (poll=%.1fs)",
                len(state.mtimes), poll_seconds)

    while True:
        if stop_event is not None and stop_event.is_set():
            return
        try:
            await asyncio.sleep(poll_seconds)
        except asyncio.CancelledError:
            return

        try:
            current = _snapshot(_manifest_paths(project_root))
        except Exception as exc:  # noqa: BLE001
            logger.warning("hot-reload snapshot failed: %s", exc)
            continue

        changed: list[Path] = []
        for path, mtime in current.items():
            prior = state.mtimes.get(path)
            if prior is None or mtime > prior:
                changed.append(path)
        # Also treat removed manifests as "change" so loader can prune.
        for path in list(state.mtimes):
            if path not in current:
                changed.append(path)

        if not changed:
            continue

        state.mtimes = current
        try:
            await _reload_cycle(pool, project_root, changed)
        except asyncio.CancelledError:
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("hot-reload cycle raised: %s", exc)

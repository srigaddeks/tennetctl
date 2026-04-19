# Phase 37 SUMMARY — DX + Catalog Hot-Reload

**Status:** ✅ Complete (2026-04-18)

## What shipped

### Handler class caching in runner

`backend/01_catalog/runner.py` — added module-level `_HANDLER_CACHE: dict[str, type]` + `invalidate_handlers(key=None)` helper.

`_resolve_handler` now:
1. Checks the cache first — zero-cost dict lookup
2. Falls through to the manifest walk + importlib only on cache miss
3. Stores the resolved handler class back into the cache on success

Previously every `run_node(key, ...)` call walked all manifests (O(features)) and re-ran `_handler_import_path()` + `importlib.import_module()`. For the hot path this was ~dozens of syscalls per audit emission.

### Dev hot-reload watcher

`backend/01_catalog/hot_reload.py` — polling-based mtime watcher spawned from the FastAPI lifespan **only when `DEBUG=true`**.

Loop:
1. Snapshot every feature manifest's mtime (1s default poll interval)
2. Detect changes (modified or removed)
3. `runner.invalidate_handlers()` — wipe the handler cache
4. `importlib.reload()` each handler module referenced by changed manifests
5. Call `loader.boot_load(pool, project_root)` to re-upsert catalog rows

Errors in any step are logged + swallowed (dev tool — broken manifest shouldn't kill the backend).

### Lifespan integration

`backend/main.py` lifespan — added start + stop wiring:

```python
# Start:
if getattr(config, "debug", False):
    _hot_reload_task = asyncio.create_task(_hot_reload.watch_manifests(pool))

# Stop:
if _hot_reload_task is not None:
    _hot_reload_task.cancel()
    await asyncio.gather(_hot_reload_task, return_exceptions=True)
```

## Why polling not watchdog

The project's env-var allowlist is strict (5 whitelisted TENNETCTL_* vars; any extras fail startup). Adding a watchdog library dependency also increases supply-chain surface. A 1-second mtime poll is cheap, requires zero new runtime deps, and the cost is paid only when `DEBUG=true`.

If sub-second freshness becomes necessary, a watchdog-backed `WatcherAdapter` protocol can slot in later without touching the runner cache layer.

## Verification

```
.venv/bin/python -m pytest tests/test_catalog_hot_reload.py -v
```

Result:
```
7 passed in 0.40s
  test_invalidate_handlers_clears_all        ✅
  test_invalidate_handlers_by_key            ✅
  test_invalidate_handlers_missing_key_is_noop ✅
  test_snapshot_returns_mtimes               ✅
  test_snapshot_skips_missing                ✅
  test_watch_respects_stop_event             ✅
  test_watch_cancellation_returns_cleanly    ✅
```

## Deferred (to later v0.1.8 phases)

- **Pre-commit hook wiring for the cross-import linter** (Phase 39 territory)
- **Versioning pattern demo** (Phase 39)
- **NCP §9 + §11 doc sync** (Phase 39)
- **Bulk ops (`get_many`) pattern docs** (Phase 39)
- **`pool` as first-class NodeContext field** (minor; NCP v2 timeframe)

## Files

| File | Action |
|---|---|
| `backend/01_catalog/runner.py` | + `_HANDLER_CACHE` + `invalidate_handlers()` + cache check in `_resolve_handler` |
| `backend/01_catalog/hot_reload.py` | NEW — polling watcher, 150 lines |
| `backend/main.py` | +lifespan start/stop for hot-reload task |
| `tests/test_catalog_hot_reload.py` | NEW — 7 tests |

"""Tests for catalog runner handler cache + hot-reload watcher helpers.

These tests exercise the pure-Python caching + file-snapshot code paths
without touching the database or network. Full integration (boot-load on
mtime bump) is covered indirectly by manual dev-mode testing.
"""

from __future__ import annotations

import asyncio
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest

_runner: Any = import_module("backend.01_catalog.runner")
_hot_reload: Any = import_module("backend.01_catalog.hot_reload")


# ---------------------------------------------------------------- handler cache


def test_invalidate_handlers_clears_all():
    _runner._HANDLER_CACHE.clear()
    _runner._HANDLER_CACHE["iam.users.get"] = object
    _runner._HANDLER_CACHE["audit.events.emit"] = object
    assert len(_runner._HANDLER_CACHE) == 2

    _runner.invalidate_handlers()

    assert _runner._HANDLER_CACHE == {}


def test_invalidate_handlers_by_key():
    _runner._HANDLER_CACHE.clear()
    _runner._HANDLER_CACHE["iam.users.get"] = object
    _runner._HANDLER_CACHE["audit.events.emit"] = object

    _runner.invalidate_handlers("iam.users.get")

    assert "iam.users.get" not in _runner._HANDLER_CACHE
    assert "audit.events.emit" in _runner._HANDLER_CACHE


def test_invalidate_handlers_missing_key_is_noop():
    _runner._HANDLER_CACHE.clear()
    # Should not raise
    _runner.invalidate_handlers("never.cached.node")


# ---------------------------------------------------------------- snapshot helper


def test_snapshot_returns_mtimes(tmp_path: Path):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("a: 1")
    b.write_text("b: 2")

    snapshot = _hot_reload._snapshot([a, b])

    assert set(snapshot.keys()) == {a, b}
    assert all(isinstance(v, float) for v in snapshot.values())


def test_snapshot_skips_missing(tmp_path: Path):
    a = tmp_path / "a.yaml"
    missing = tmp_path / "missing.yaml"
    a.write_text("a: 1")

    snapshot = _hot_reload._snapshot([a, missing])

    assert a in snapshot
    assert missing not in snapshot


# ---------------------------------------------------------------- watch loop


@pytest.mark.asyncio
async def test_watch_respects_stop_event(tmp_path: Path):
    """watch_manifests should honor stop_event and return promptly."""
    (tmp_path / "02_features").mkdir()  # give discover_manifests a clean empty tree

    stop = asyncio.Event()
    task = asyncio.create_task(
        _hot_reload.watch_manifests(
            pool=None,  # pool only touched on actual reload; no changes means no touch
            project_root=tmp_path,
            poll_seconds=0.05,
            stop_event=stop,
        )
    )

    await asyncio.sleep(0.1)
    stop.set()
    await asyncio.wait_for(task, timeout=1.0)
    # If we got here without timeout, watcher honored stop_event.


@pytest.mark.asyncio
async def test_watch_cancellation_returns_cleanly(tmp_path: Path):
    """Cancelling the watcher task should not leak exceptions."""
    (tmp_path / "02_features").mkdir()

    task = asyncio.create_task(
        _hot_reload.watch_manifests(
            pool=None,
            project_root=tmp_path,
            poll_seconds=0.05,
        )
    )
    await asyncio.sleep(0.1)
    task.cancel()

    # Swallow CancelledError quietly (which is what the watcher returns on cancel)
    try:
        await task
    except asyncio.CancelledError:
        pass

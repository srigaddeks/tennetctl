"""Unit tests for WorkerPool — supervisor lifecycle + restart-on-crash."""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any
from unittest.mock import MagicMock

_runner_mod: Any = import_module("backend.02_features.05_monitoring.workers.runner")
WorkerPool = _runner_mod.WorkerPool


class _FakePool:
    """Minimal pool stub — the scraper/consumer factories don't hit DB in these tests."""


def _make_config(apisix_enabled: bool = False) -> Any:
    c = MagicMock()
    c.monitoring_apisix_scrape_enabled = apisix_enabled
    c.monitoring_consumer_batch_size = 200
    c.monitoring_consumer_max_deliver = 5
    c.monitoring_store_kind = "postgres"
    c.monitoring_apisix_url = "http://test/metrics"
    # 13-07 workers — disabled in this test suite
    c.monitoring_rollup_enabled = False
    c.monitoring_partition_manager_enabled = False
    c.monitoring_synthetic_runner_enabled = False
    c.monitoring_notify_listener_enabled = False
    c.monitoring_alert_evaluator_enabled = False
    return c


async def test_start_stop_cleanly_with_no_js():
    """With js=None and apisix disabled, WorkerPool should start with zero tasks."""
    pool = WorkerPool()
    await pool.start(pool=_FakePool(), js=None, config=_make_config(apisix_enabled=False))
    assert pool._tasks == []
    await pool.stop(timeout=1.0)


async def test_supervisor_restarts_on_crash():
    """A worker that raises should be restarted; restart_count increments."""
    pool = WorkerPool()
    pool._backoff_override = (0.01, 0.01, 0.01, 0.01)
    pool._states["test_worker"] = _runner_mod.WorkerState("test_worker")

    attempts = {"n": 0}

    async def _crasher():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("boom")
        # Third attempt succeeds and returns normally.
        return None

    task = asyncio.create_task(pool._supervised("test_worker", _crasher))
    await asyncio.wait_for(task, timeout=2.0)
    state = pool._states["test_worker"]
    assert attempts["n"] == 3
    assert state.restart_count == 2


async def test_stop_cancels_running_workers():
    """stop() should cancel in-flight worker tasks within the timeout."""
    pool = WorkerPool()
    pool._backoff_override = (0.01,)
    pool._states["sleeper"] = _runner_mod.WorkerState("sleeper")

    async def _sleeper():
        await asyncio.sleep(100)

    task = asyncio.create_task(pool._supervised("sleeper", _sleeper))
    pool._tasks.append(task)
    # Give the task a moment to enter the sleep.
    await asyncio.sleep(0.05)
    await pool.stop(timeout=2.0)
    assert task.done()


async def test_health_returns_per_worker_snapshot():
    pool = WorkerPool()
    pool._states["w1"] = _runner_mod.WorkerState("w1")
    pool._states["w2"] = _runner_mod.WorkerState("w2")
    pool._states["w1"].restart_count = 3
    h = pool.health()
    assert "w1" in h and "w2" in h
    assert h["w1"]["restart_count"] == 3
    assert h["w1"]["running"] is False

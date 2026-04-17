"""SDK tests for monitoring.sdk.metrics — first-use register + caching + disabled."""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any
from unittest.mock import patch

import pytest

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_ctx_mod: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")
_sdk: Any = import_module("backend.02_features.05_monitoring.sdk.metrics")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.02_metrics.service"
)

_ORG_ID = "019e0000-4444-7000-0000-000000000001"
_USER_ID = "019e0000-4444-7000-0000-000000000003"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "05_monitoring"."61_evt_monitoring_metric_points" '
            'WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "05_monitoring"."10_fct_monitoring_metrics" '
            'WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "05_monitoring"."11_fct_monitoring_resources" '
            'WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "04_audit"."60_evt_audit" WHERE actor_user_id = $1',
            _USER_ID,
        )
    _service._cache_clear()
    _sdk._reset_sdk_cache()


def _ctx(pool: Any) -> Any:
    return _ctx_mod.NodeContext(
        user_id=_USER_ID,
        session_id=_USER_ID,
        org_id=_ORG_ID,
        workspace_id=None,
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(),
        audit_category="setup",
        extras={"pool": pool},
    )


@pytest.fixture
async def live_pool():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        try:
            yield pool
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


@pytest.mark.asyncio
async def test_counter_first_use_registers_and_caches(live_pool):
    pool = live_pool
    ctx = _ctx(pool)
    c = _sdk.counter("sdk.cnt", labels=["outcome"], description="sdk test")
    await c.increment(ctx, labels={"outcome": "success"})
    async with pool.acquire() as conn:
        n = await conn.fetchval(
            'SELECT COUNT(*) FROM "05_monitoring"."10_fct_monitoring_metrics" '
            'WHERE org_id = $1 AND key = $2',
            _ORG_ID, "sdk.cnt",
        )
    assert int(n) == 1
    # Second call doesn't re-register — cache hit.
    assert (str(_ORG_ID), "sdk.cnt") in _sdk._registered
    await c.increment(ctx, labels={"outcome": "success"})
    async with pool.acquire() as conn:
        n2 = await conn.fetchval(
            'SELECT COUNT(*) FROM "05_monitoring"."10_fct_monitoring_metrics" '
            'WHERE org_id = $1 AND key = $2',
            _ORG_ID, "sdk.cnt",
        )
    assert int(n2) == 1


@pytest.mark.asyncio
async def test_concurrent_first_use_registers_once(live_pool):
    pool = live_pool
    ctx = _ctx(pool)
    c = _sdk.counter("sdk.concurrent", labels=["k"])
    results = await asyncio.gather(
        c.increment(ctx, labels={"k": "a"}),
        c.increment(ctx, labels={"k": "b"}),
        c.increment(ctx, labels={"k": "c"}),
    )
    assert all(r is None for r in results)
    async with pool.acquire() as conn:
        n = await conn.fetchval(
            'SELECT COUNT(*) FROM "05_monitoring"."10_fct_monitoring_metrics" '
            'WHERE org_id = $1 AND key = $2',
            _ORG_ID, "sdk.concurrent",
        )
    assert int(n) == 1


@pytest.mark.asyncio
async def test_disabled_module_is_noop(live_pool):
    pool = live_pool
    ctx = _ctx(pool)
    c = _sdk.counter("sdk.disabled", labels=[])
    with patch.object(_sdk, "_enabled", return_value=False):
        await c.increment(ctx)
    # No metric registered; no points written.
    async with pool.acquire() as conn:
        n = await conn.fetchval(
            'SELECT COUNT(*) FROM "05_monitoring"."10_fct_monitoring_metrics" '
            'WHERE org_id = $1 AND key = $2',
            _ORG_ID, "sdk.disabled",
        )
    assert int(n) == 0


@pytest.mark.asyncio
async def test_gauge_and_histogram_handles_work(live_pool):
    pool = live_pool
    ctx = _ctx(pool)
    g = _sdk.gauge("sdk.g", labels=["host"])
    await g.set(ctx, value=42.0, labels={"host": "h1"})

    h = _sdk.histogram("sdk.h", buckets=[1.0, 5.0, 10.0], labels=[])
    await h.observe(ctx, value=0.5)

    async with pool.acquire() as conn:
        keys = await conn.fetch(
            'SELECT key FROM "05_monitoring"."10_fct_monitoring_metrics" '
            'WHERE org_id = $1 ORDER BY key',
            _ORG_ID,
        )
    assert {r["key"] for r in keys} == {"sdk.g", "sdk.h"}

"""Node-dispatch tests for monitoring.metrics.* via run_node + NodeContext."""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import pytest

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_ctx_mod: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.02_metrics.service"
)

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0000-3333-7000-0000-000000000001"
_USER_ID = "019e0000-3333-7000-0000-000000000003"


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


def _ctx(pool: Any) -> Any:
    return _ctx_mod.NodeContext(
        user_id=_USER_ID,
        session_id=_USER_ID,  # stand-in
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
async def test_register_node_emits_audit(live_pool):
    pool = live_pool
    ctx = _ctx(pool)
    result = await _catalog.run_node(
        pool, "monitoring.metrics.register", ctx,
        {
            "org_id": _ORG_ID,
            "key": "node.test.cnt",
            "kind": "counter",
            "label_keys": ["k"],
            "max_cardinality": 10,
        },
    )
    assert "metric_id" in result
    async with pool.acquire() as conn:
        n = await conn.fetchval(
            'SELECT COUNT(*) FROM "04_audit"."60_evt_audit" '
            "WHERE event_key = 'monitoring.metrics.registered' AND actor_user_id = $1",
            _USER_ID,
        )
    assert int(n) >= 1


@pytest.mark.asyncio
async def test_increment_node_appends_point(live_pool):
    pool = live_pool
    ctx = _ctx(pool)
    await _catalog.run_node(
        pool, "monitoring.metrics.register", ctx,
        {
            "org_id": _ORG_ID, "key": "node.inc", "kind": "counter",
            "label_keys": ["route"], "max_cardinality": 10,
        },
    )
    res = await _catalog.run_node(
        pool, "monitoring.metrics.increment", ctx,
        {
            "org_id": _ORG_ID, "metric_key": "node.inc",
            "labels": {"route": "/v1/x"}, "value": 1.0,
        },
    )
    assert res["accepted"] is True
    async with pool.acquire() as conn:
        n = await conn.fetchval(
            'SELECT COUNT(*) FROM "05_monitoring"."61_evt_monitoring_metric_points" '
            'WHERE org_id = $1',
            _ORG_ID,
        )
    assert int(n) == 1


@pytest.mark.asyncio
async def test_gauge_node_set(live_pool):
    pool = live_pool
    ctx = _ctx(pool)
    await _catalog.run_node(
        pool, "monitoring.metrics.register", ctx,
        {
            "org_id": _ORG_ID, "key": "node.g", "kind": "gauge",
            "label_keys": ["host"],
        },
    )
    res = await _catalog.run_node(
        pool, "monitoring.metrics.set_gauge", ctx,
        {
            "org_id": _ORG_ID, "metric_key": "node.g",
            "labels": {"host": "h1"}, "value": 42.5,
        },
    )
    assert res["accepted"] is True


@pytest.mark.asyncio
async def test_cardinality_reject_via_node_emits_failure_audit(live_pool):
    pool = live_pool
    ctx = _ctx(pool)
    await _catalog.run_node(
        pool, "monitoring.metrics.register", ctx,
        {
            "org_id": _ORG_ID, "key": "node.card", "kind": "counter",
            "label_keys": ["k"], "max_cardinality": 1,
        },
    )
    await _catalog.run_node(
        pool, "monitoring.metrics.increment", ctx,
        {
            "org_id": _ORG_ID, "metric_key": "node.card",
            "labels": {"k": "a"}, "value": 1.0,
        },
    )
    with pytest.raises(Exception):
        await _catalog.run_node(
            pool, "monitoring.metrics.increment", ctx,
            {
                "org_id": _ORG_ID, "metric_key": "node.card",
                "labels": {"k": "b"}, "value": 1.0,
            },
        )
    async with pool.acquire() as conn:
        n = await conn.fetchval(
            'SELECT COUNT(*) FROM "04_audit"."60_evt_audit" '
            "WHERE event_key = 'monitoring.metrics.cardinality_exceeded'",
        )
    assert int(n) >= 1

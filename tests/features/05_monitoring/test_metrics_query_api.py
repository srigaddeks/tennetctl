"""Integration tests for POST /v1/monitoring/metrics/query."""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.02_metrics.service"
)

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0000-5555-7000-0000-000000000001"
_WS_ID = "019e0000-5555-7000-0000-000000000002"
_USER_ID = "019e0000-5555-7000-0000-000000000003"
_SESSION_ID = "019e0000-5555-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID,
    "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID,
    "x-session-id": _SESSION_ID,
}


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "05_monitoring"."61_evt_monitoring_metric_points" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "05_monitoring"."10_fct_monitoring_metrics" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "05_monitoring"."11_fct_monitoring_resources" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "04_audit"."60_evt_audit" WHERE actor_user_id = $1',
            _USER_ID,
        )
    _service._cache_clear()


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(
                transport=transport, base_url="http://test", headers=_HDR,
            ) as ac:
                yield ac, pool
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


async def _register_and_increment(client: AsyncClient) -> None:
    r = await client.post("/v1/monitoring/metrics", json={
        "key": "query.test.hits",
        "kind": "counter",
        "label_keys": ["endpoint"],
        "max_cardinality": 100,
    })
    assert r.status_code == 201, r.text
    for _ in range(3):
        r2 = await client.post(
            "/v1/monitoring/metrics/query.test.hits/increment",
            json={"labels": {"endpoint": "/foo"}, "value": 1.0},
        )
        assert r2.status_code == 201, r2.text


@pytest.mark.asyncio
async def test_metrics_query_sum(live_app):
    client, _pool = live_app
    await _register_and_increment(client)
    r = await client.post("/v1/monitoring/metrics/query", json={
        "target": "metrics",
        "metric_key": "query.test.hits",
        "timerange": {"last": "1h"},
        "aggregate": "sum",
        "bucket": "1m",
    })
    assert r.status_code == 200, r.text
    items = r.json()["data"]["items"]
    assert len(items) >= 1
    # Sum of 3 increments of value=1.0 should be >= 3 (possibly in a single bucket).
    total = sum(float(row["value"] or 0) for row in items)
    assert total >= 3.0


@pytest.mark.asyncio
async def test_metrics_query_count(live_app):
    client, _pool = live_app
    await _register_and_increment(client)
    r = await client.post("/v1/monitoring/metrics/query", json={
        "target": "metrics",
        "metric_key": "query.test.hits",
        "timerange": {"last": "1h"},
        "aggregate": "count",
        "bucket": "1m",
    })
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_metrics_query_labels_filter(live_app):
    client, _pool = live_app
    await _register_and_increment(client)
    r = await client.post("/v1/monitoring/metrics/query", json={
        "target": "metrics",
        "metric_key": "query.test.hits",
        "timerange": {"last": "1h"},
        "labels": {"endpoint": "/foo"},
        "aggregate": "sum",
        "bucket": "1m",
    })
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_metrics_query_invalid_bucket(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/metrics/query", json={
        "target": "metrics",
        "metric_key": "foo",
        "timerange": {"last": "1h"},
        "bucket": "13m",
    })
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_metrics_query_unknown_metric_returns_empty(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/metrics/query", json={
        "target": "metrics",
        "metric_key": "does.not.exist",
        "timerange": {"last": "1h"},
        "aggregate": "sum",
    })
    assert r.status_code == 200, r.text
    assert r.json()["data"]["items"] == []


@pytest.mark.asyncio
async def test_metrics_query_cross_org_isolation(live_app):
    client, _pool = live_app
    await _register_and_increment(client)
    other = dict(_HDR)
    other["x-org-id"] = "019e0000-5555-7000-0000-999999999999"
    other["x-user-id"] = "019e0000-5555-7000-0000-999999999998"
    other["x-session-id"] = "019e0000-5555-7000-0000-999999999997"
    r = await client.post(
        "/v1/monitoring/metrics/query",
        json={
            "target": "metrics",
            "metric_key": "query.test.hits",
            "timerange": {"last": "1h"},
            "aggregate": "sum",
        },
        headers=other,
    )
    assert r.status_code == 200
    assert r.json()["data"]["items"] == []

"""REST API tests for monitoring.metrics — register/list/get/increment/set/observe.

Uses the live DB (DATABASE_URL). Each test cleans its own org scope.
"""

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

_ORG_ID = "019e0000-2222-7000-0000-000000000001"
_WS_ID = "019e0000-2222-7000-0000-000000000002"
_USER_ID = "019e0000-2222-7000-0000-000000000003"
_SESSION_ID = "019e0000-2222-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID,
    "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID,
    "x-session-id": _SESSION_ID,
}


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


@pytest.mark.asyncio
async def test_register_counter_success(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/metrics", json={
        "key": "test.requests",
        "kind": "counter",
        "label_keys": ["endpoint"],
        "description": "test counter",
        "max_cardinality": 100,
    })
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["key"] == "test.requests"
    assert data["kind"] == "counter"
    assert data["label_keys"] == ["endpoint"]


@pytest.mark.asyncio
async def test_register_histogram_requires_buckets(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/metrics", json={
        "key": "test.latency",
        "kind": "histogram",
        "label_keys": [],
    })
    assert r.status_code == 422, r.text


@pytest.mark.asyncio
async def test_register_counter_rejects_buckets(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/metrics", json={
        "key": "test.bad_counter",
        "kind": "counter",
        "histogram_buckets": [1.0, 2.0],
    })
    assert r.status_code == 422, r.text


@pytest.mark.asyncio
async def test_register_idempotent(live_app):
    client, _pool = live_app
    body = {
        "key": "test.idem",
        "kind": "counter",
        "label_keys": ["k"],
    }
    r1 = await client.post("/v1/monitoring/metrics", json=body)
    assert r1.status_code == 201
    mid1 = r1.json()["data"]["id"]
    r2 = await client.post("/v1/monitoring/metrics", json=body)
    assert r2.status_code == 201
    mid2 = r2.json()["data"]["id"]
    assert mid1 == mid2


@pytest.mark.asyncio
async def test_list_and_get(live_app):
    client, _pool = live_app
    await client.post("/v1/monitoring/metrics", json={
        "key": "test.ls1", "kind": "counter", "label_keys": [],
    })
    await client.post("/v1/monitoring/metrics", json={
        "key": "test.ls2", "kind": "gauge", "label_keys": [],
    })
    r = await client.get("/v1/monitoring/metrics")
    assert r.status_code == 200
    data = r.json()["data"]
    keys = {m["key"] for m in data["items"]}
    assert {"test.ls1", "test.ls2"}.issubset(keys)

    r = await client.get("/v1/monitoring/metrics/test.ls1")
    assert r.status_code == 200
    assert r.json()["data"]["kind"] == "counter"

    r = await client.get("/v1/monitoring/metrics/test.does-not-exist")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_counter_increment_and_cardinality_reject(live_app):
    client, pool = live_app
    r = await client.post("/v1/monitoring/metrics", json={
        "key": "test.cnt",
        "kind": "counter",
        "label_keys": ["k"],
        "max_cardinality": 2,
    })
    assert r.status_code == 201

    # Two accepted combos.
    for label_val in ("a", "b"):
        r = await client.post(
            "/v1/monitoring/metrics/test.cnt/increment",
            json={"labels": {"k": label_val}, "value": 1.0},
        )
        assert r.status_code == 201, r.text

    # Third distinct combo → 429.
    r = await client.post(
        "/v1/monitoring/metrics/test.cnt/increment",
        json={"labels": {"k": "c"}, "value": 1.0},
    )
    assert r.status_code == 429, r.text
    assert r.json()["error"]["code"] == "CARDINALITY_EXCEEDED"

    # Existing combo still accepted.
    r = await client.post(
        "/v1/monitoring/metrics/test.cnt/increment",
        json={"labels": {"k": "a"}, "value": 1.0},
    )
    assert r.status_code == 201, r.text

    # Failure audit was written.
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT COUNT(*)::INT AS n FROM "04_audit"."60_evt_audit" '
            "WHERE event_key = 'monitoring.metrics.cardinality_exceeded'",
        )
        assert row is not None and int(row["n"]) >= 1


@pytest.mark.asyncio
async def test_counter_rejects_negative_and_bad_labels(live_app):
    client, _pool = live_app
    await client.post("/v1/monitoring/metrics", json={
        "key": "test.negcnt", "kind": "counter", "label_keys": ["k"],
    })
    r = await client.post(
        "/v1/monitoring/metrics/test.negcnt/increment",
        json={"labels": {"k": "a"}, "value": -1.0},
    )
    assert r.status_code == 422, r.text
    r = await client.post(
        "/v1/monitoring/metrics/test.negcnt/increment",
        json={"labels": {"not_registered": "x"}, "value": 1.0},
    )
    assert r.status_code == 422, r.text


@pytest.mark.asyncio
async def test_gauge_set_allows_negative(live_app):
    client, _pool = live_app
    await client.post("/v1/monitoring/metrics", json={
        "key": "test.g", "kind": "gauge", "label_keys": ["host"],
    })
    r = await client.post(
        "/v1/monitoring/metrics/test.g/set",
        json={"labels": {"host": "h1"}, "value": -5.0},
    )
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_histogram_observe_writes_buckets(live_app):
    client, pool = live_app
    await client.post("/v1/monitoring/metrics", json={
        "key": "test.h",
        "kind": "histogram",
        "label_keys": [],
        "histogram_buckets": [1.0, 5.0, 10.0],
    })
    r = await client.post(
        "/v1/monitoring/metrics/test.h/observe",
        json={"labels": {}, "value": 0.5},
    )
    assert r.status_code == 201, r.text
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT histogram_counts, histogram_sum, histogram_count '
            'FROM "05_monitoring"."61_evt_monitoring_metric_points" '
            'WHERE org_id = $1 ORDER BY recorded_at DESC LIMIT 1',
            _ORG_ID,
        )
    assert row is not None
    counts = list(row["histogram_counts"])
    assert counts[0] == 1
    assert sum(counts) == 1


@pytest.mark.asyncio
async def test_increment_on_gauge_is_rejected(live_app):
    client, _pool = live_app
    await client.post("/v1/monitoring/metrics", json={
        "key": "test.g2", "kind": "gauge", "label_keys": [],
    })
    r = await client.post(
        "/v1/monitoring/metrics/test.g2/increment",
        json={"labels": {}, "value": 1.0},
    )
    assert r.status_code == 422, r.text

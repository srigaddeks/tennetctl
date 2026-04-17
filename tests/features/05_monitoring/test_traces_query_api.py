"""Integration tests for POST /v1/monitoring/traces/query and GET /traces/{trace_id}."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_stores: Any = import_module("backend.02_features.05_monitoring.stores")
_types: Any = import_module("backend.02_features.05_monitoring.stores.types")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0000-6666-7000-0000-000000000001"
_WS_ID = "019e0000-6666-7000-0000-000000000002"
_USER_ID = "019e0000-6666-7000-0000-000000000003"
_SESSION_ID = "019e0000-6666-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID,
    "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID,
    "x-session-id": _SESSION_ID,
}


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "05_monitoring"."62_evt_monitoring_spans" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "05_monitoring"."11_fct_monitoring_resources" WHERE org_id = $1',
            _ORG_ID,
        )


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _seed_spans(pool: Any, trace_id: str, n: int = 3) -> None:
    async with pool.acquire() as conn:
        rstore = _stores.get_resources_store(pool)
        rid = await rstore.upsert(conn, _types.ResourceRecord(
            org_id=_ORG_ID,
            service_name="trace-test-svc",
            service_instance_id=None,
            service_version=None,
            attributes={},
        ))
        sstore = _stores.get_spans_store(pool)
        records = []
        parent = None
        base_ns = 1_713_350_000_000_000_000
        for i in range(n):
            span_id = f"{i:016x}"
            start = base_ns + i * 1_000_000
            end = start + 500_000
            records.append(_types.SpanRecord(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent,
                org_id=_ORG_ID,
                workspace_id=_WS_ID,
                resource_id=rid,
                name=f"GET /endpoint/{i}",
                kind_id=1,
                status_id=1,
                status_message=None,
                recorded_at=_now(),
                start_time_unix_nano=start,
                end_time_unix_nano=end,
                attributes={"idx": i},
                events=[],
                links=[],
            ))
            parent = span_id
        await sstore.insert_batch(conn, records)


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
async def test_traces_query_happy_path(live_app):
    client, pool = live_app
    await _seed_spans(pool, "a" * 32, n=3)
    r = await client.post("/v1/monitoring/traces/query", json={
        "target": "traces",
        "timerange": {"last": "24h"},
        "limit": 100,
    })
    assert r.status_code == 200, r.text
    items = r.json()["data"]["items"]
    assert len(items) >= 3


@pytest.mark.asyncio
async def test_traces_query_span_name_contains(live_app):
    client, pool = live_app
    await _seed_spans(pool, "b" * 32, n=2)
    r = await client.post("/v1/monitoring/traces/query", json={
        "target": "traces",
        "timerange": {"last": "24h"},
        "span_name_contains": "GET",
    })
    assert r.status_code == 200
    for s in r.json()["data"]["items"]:
        assert "GET" in s["name"]


@pytest.mark.asyncio
async def test_traces_detail_endpoint(live_app):
    client, pool = live_app
    trace_id = "c" * 32
    await _seed_spans(pool, trace_id, n=3)
    r = await client.get(f"/v1/monitoring/traces/{trace_id}")
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["trace_id"] == trace_id
    assert len(data["spans"]) == 3


@pytest.mark.asyncio
async def test_traces_invalid_dsl_400(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/traces/query", json={
        "target": "traces",
        # missing timerange
    })
    assert r.status_code == 400

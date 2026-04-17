"""Integration tests for POST /v1/monitoring/logs/query.

Seeds logs directly into v_monitoring_logs backing tables via the Postgres
store, then exercises the HTTP query endpoint.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_core_id: Any = import_module("backend.01_core.id")
_stores: Any = import_module("backend.02_features.05_monitoring.stores")
_types: Any = import_module("backend.02_features.05_monitoring.stores.types")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0000-4444-7000-0000-000000000001"
_WS_ID = "019e0000-4444-7000-0000-000000000002"
_USER_ID = "019e0000-4444-7000-0000-000000000003"
_SESSION_ID = "019e0000-4444-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID,
    "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID,
    "x-session-id": _SESSION_ID,
}


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "05_monitoring"."60_evt_monitoring_logs" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "05_monitoring"."11_fct_monitoring_resources" WHERE org_id = $1',
            _ORG_ID,
        )


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _seed_logs(pool: Any, n: int = 3) -> list[str]:
    """Seed a handful of log rows, return ids (in insertion order)."""
    ids: list[str] = []
    async with pool.acquire() as conn:
        # resource
        rstore = _stores.get_resources_store(pool)
        rid = await rstore.upsert(conn, _types.ResourceRecord(
            org_id=_ORG_ID,
            service_name="test-service",
            service_instance_id=None,
            service_version=None,
            attributes={},
        ))
        lstore = _stores.get_logs_store(pool)
        records = []
        for i in range(n):
            log_id = _core_id.uuid7()
            ids.append(log_id)
            records.append(_types.LogRecord(
                id=log_id,
                org_id=_ORG_ID,
                workspace_id=_WS_ID,
                resource_id=rid,
                recorded_at=_now(),
                observed_at=_now(),
                severity_id=17,
                severity_text="ERROR",
                body=f"seeded log message {i}",
                trace_id=None,
                span_id=None,
                trace_flags=None,
                scope_name=None,
                scope_version=None,
                attributes={"seq": i},
                dropped_attributes_count=0,
            ))
        await lstore.insert_batch(conn, records)
    return ids


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
async def test_logs_query_happy_path(live_app):
    client, pool = live_app
    await _seed_logs(pool, n=3)
    r = await client.post("/v1/monitoring/logs/query", json={
        "target": "logs",
        "timerange": {"last": "24h"},
        "limit": 10,
    })
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert len(data["items"]) >= 3


@pytest.mark.asyncio
async def test_logs_query_severity_filter(live_app):
    client, pool = live_app
    await _seed_logs(pool, n=2)
    r = await client.post("/v1/monitoring/logs/query", json={
        "target": "logs",
        "timerange": {"last": "24h"},
        "severity_min": 17,
        "limit": 50,
    })
    assert r.status_code == 200, r.text
    for row in r.json()["data"]["items"]:
        assert row["severity_id"] >= 17


@pytest.mark.asyncio
async def test_logs_query_body_contains(live_app):
    client, pool = live_app
    await _seed_logs(pool, n=3)
    r = await client.post("/v1/monitoring/logs/query", json={
        "target": "logs",
        "timerange": {"last": "24h"},
        "body_contains": "seeded",
        "limit": 50,
    })
    assert r.status_code == 200, r.text
    items = r.json()["data"]["items"]
    assert len(items) >= 3
    for row in items:
        assert "seeded" in row["body"]


@pytest.mark.asyncio
async def test_logs_query_invalid_dsl_400(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/logs/query", json={
        "target": "logs",
        "timerange": {"last": "999d"},
    })
    assert r.status_code == 400, r.text
    assert r.json()["ok"] is False


@pytest.mark.asyncio
async def test_logs_query_cross_org_isolation(live_app):
    client, pool = live_app
    await _seed_logs(pool, n=2)
    # Different org — should see zero rows.
    other_hdr = dict(_HDR)
    other_hdr["x-org-id"] = "019e0000-4444-7000-0000-999999999999"
    other_hdr["x-user-id"] = "019e0000-4444-7000-0000-999999999998"
    other_hdr["x-session-id"] = "019e0000-4444-7000-0000-999999999997"
    r = await client.post(
        "/v1/monitoring/logs/query",
        json={"target": "logs", "timerange": {"last": "24h"}},
        headers=other_hdr,
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["items"] == []


@pytest.mark.asyncio
async def test_logs_query_regex_rejected(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/logs/query", json={
        "target": "logs",
        "timerange": {"last": "1h"},
        "filter": {"regex_limited": {"field": "body", "value": "a" * 200}},
    })
    assert r.status_code == 400, r.text

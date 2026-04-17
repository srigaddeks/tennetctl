"""Integration tests for monitoring.saved_queries CRUD + run."""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0000-7777-7000-0000-000000000001"
_WS_ID = "019e0000-7777-7000-0000-000000000002"
_USER_ID = "019e0000-7777-7000-0000-000000000003"
_SESSION_ID = "019e0000-7777-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID,
    "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID,
    "x-session-id": _SESSION_ID,
}


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "05_monitoring"."10_fct_monitoring_saved_queries" WHERE org_id = $1',
            _ORG_ID,
        )


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


_DSL_LOGS = {
    "target": "logs",
    "timerange": {"last": "1h"},
    "severity_min": 17,
    "limit": 10,
}


@pytest.mark.asyncio
async def test_saved_query_create(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/saved-queries", json={
        "name": "recent errors",
        "target": "logs",
        "dsl": _DSL_LOGS,
    })
    assert r.status_code == 201, r.text
    body = r.json()["data"]
    assert body["name"] == "recent errors"
    assert body["target"] == "logs"
    assert body["owner_user_id"] == _USER_ID


@pytest.mark.asyncio
async def test_saved_query_list(live_app):
    client, _pool = live_app
    await client.post("/v1/monitoring/saved-queries", json={
        "name": "q1", "target": "logs", "dsl": _DSL_LOGS,
    })
    await client.post("/v1/monitoring/saved-queries", json={
        "name": "q2", "target": "logs", "dsl": _DSL_LOGS,
    })
    r = await client.get("/v1/monitoring/saved-queries")
    assert r.status_code == 200
    assert r.json()["data"]["total"] >= 2


@pytest.mark.asyncio
async def test_saved_query_get(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/saved-queries", json={
        "name": "getme", "target": "logs", "dsl": _DSL_LOGS,
    })
    sq_id = r.json()["data"]["id"]
    r2 = await client.get(f"/v1/monitoring/saved-queries/{sq_id}")
    assert r2.status_code == 200
    assert r2.json()["data"]["id"] == sq_id


@pytest.mark.asyncio
async def test_saved_query_patch(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/saved-queries", json={
        "name": "patchme", "target": "logs", "dsl": _DSL_LOGS,
    })
    sq_id = r.json()["data"]["id"]
    r2 = await client.patch(f"/v1/monitoring/saved-queries/{sq_id}", json={
        "description": "updated",
        "shared": True,
    })
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert data["description"] == "updated"
    assert data["shared"] is True


@pytest.mark.asyncio
async def test_saved_query_delete(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/saved-queries", json={
        "name": "deleteme", "target": "logs", "dsl": _DSL_LOGS,
    })
    sq_id = r.json()["data"]["id"]
    r2 = await client.delete(f"/v1/monitoring/saved-queries/{sq_id}")
    assert r2.status_code == 204
    r3 = await client.get(f"/v1/monitoring/saved-queries/{sq_id}")
    assert r3.status_code == 404


@pytest.mark.asyncio
async def test_saved_query_run(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/saved-queries", json={
        "name": "run-it", "target": "logs", "dsl": _DSL_LOGS,
    })
    sq_id = r.json()["data"]["id"]
    r2 = await client.post(f"/v1/monitoring/saved-queries/{sq_id}/run")
    assert r2.status_code == 200, r2.text
    data = r2.json()["data"]
    assert data["target"] == "logs"
    assert "items" in data


@pytest.mark.asyncio
async def test_saved_query_invalid_dsl_rejected(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/saved-queries", json={
        "name": "bad", "target": "logs",
        "dsl": {"target": "logs"},  # missing timerange
    })
    assert r.status_code == 422

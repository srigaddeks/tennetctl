"""Integration tests for monitoring.dashboards CRUD."""

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

_ORG_ID = "019e0000-8888-7000-0000-000000000001"
_WS_ID = "019e0000-8888-7000-0000-000000000002"
_USER_ID = "019e0000-8888-7000-0000-000000000003"
_USER_2 = "019e0000-8888-7000-0000-000000000103"
_SESSION_ID = "019e0000-8888-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID,
    "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID,
    "x-session-id": _SESSION_ID,
}


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "05_monitoring"."11_fct_monitoring_panels" '
            'WHERE dashboard_id IN ('
            'SELECT id FROM "05_monitoring"."10_fct_monitoring_dashboards" WHERE org_id = $1)',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "05_monitoring"."10_fct_monitoring_dashboards" WHERE org_id = $1',
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


@pytest.mark.asyncio
async def test_dashboard_create_happy(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/dashboards", json={
        "name": "My Dashboard",
        "description": "first",
    })
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["name"] == "My Dashboard"
    assert data["owner_user_id"] == _USER_ID
    assert data["panel_count"] == 0


@pytest.mark.asyncio
async def test_dashboard_create_duplicate_name(live_app):
    client, _pool = live_app
    r1 = await client.post(
        "/v1/monitoring/dashboards", json={"name": "dup"},
    )
    assert r1.status_code == 201
    r2 = await client.post(
        "/v1/monitoring/dashboards", json={"name": "dup"},
    )
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_dashboard_shared_visible_to_other_user(live_app):
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/dashboards",
        json={"name": "shared", "shared": True},
    )
    assert r.status_code == 201
    other = dict(_HDR)
    other["x-user-id"] = _USER_2
    r2 = await client.get("/v1/monitoring/dashboards", headers=other)
    assert r2.status_code == 200
    names = [d["name"] for d in r2.json()["data"]["items"]]
    assert "shared" in names


@pytest.mark.asyncio
async def test_dashboard_get_includes_panels(live_app):
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/dashboards", json={"name": "d1"},
    )
    dash_id = r.json()["data"]["id"]
    await client.post(
        f"/v1/monitoring/dashboards/{dash_id}/panels",
        json={
            "title": "p1", "panel_type": "stat",
            "dsl": {"target": "metrics"},
        },
    )
    r2 = await client.get(f"/v1/monitoring/dashboards/{dash_id}")
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert len(data["panels"]) == 1
    assert data["panels"][0]["title"] == "p1"


@pytest.mark.asyncio
async def test_dashboard_update_fields(live_app):
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/dashboards", json={"name": "u1"},
    )
    dash_id = r.json()["data"]["id"]
    r2 = await client.patch(
        f"/v1/monitoring/dashboards/{dash_id}",
        json={"description": "changed", "shared": True},
    )
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert data["description"] == "changed"
    assert data["shared"] is True


@pytest.mark.asyncio
async def test_dashboard_soft_delete(live_app):
    client, pool = live_app
    r = await client.post(
        "/v1/monitoring/dashboards", json={"name": "del"},
    )
    dash_id = r.json()["data"]["id"]
    r2 = await client.delete(f"/v1/monitoring/dashboards/{dash_id}")
    assert r2.status_code == 204
    r3 = await client.get("/v1/monitoring/dashboards")
    names = [d["name"] for d in r3.json()["data"]["items"]]
    assert "del" not in names
    # Row still present in raw table.
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT deleted_at FROM "05_monitoring"."10_fct_monitoring_dashboards" WHERE id = $1',
            dash_id,
        )
        assert row is not None
        assert row["deleted_at"] is not None


@pytest.mark.asyncio
async def test_dashboard_cross_org_read_404(live_app):
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/dashboards", json={"name": "x"},
    )
    dash_id = r.json()["data"]["id"]
    other = dict(_HDR)
    other["x-org-id"] = "019e0000-8888-7000-0000-99999999aaaa"
    other["x-user-id"] = "019e0000-8888-7000-0000-99999999bbbb"
    r2 = await client.get(
        f"/v1/monitoring/dashboards/{dash_id}", headers=other,
    )
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_cross_owner_update_403(live_app):
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/dashboards",
        json={"name": "owned", "shared": True},
    )
    dash_id = r.json()["data"]["id"]
    other = dict(_HDR)
    other["x-user-id"] = _USER_2
    r2 = await client.patch(
        f"/v1/monitoring/dashboards/{dash_id}",
        json={"description": "hijack"},
        headers=other,
    )
    assert r2.status_code == 403

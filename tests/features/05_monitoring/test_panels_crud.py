"""Integration tests for monitoring.dashboards panels CRUD."""

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

_ORG_ID = "019e0000-9999-7000-0000-000000000001"
_WS_ID = "019e0000-9999-7000-0000-000000000002"
_USER_ID = "019e0000-9999-7000-0000-000000000003"
_SESSION_ID = "019e0000-9999-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID,
    "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID,
    "x-session-id": _SESSION_ID,
}

_DSL_METRICS = {"target": "metrics", "metric_key": "cpu.usage"}


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


async def _make_dashboard(client: AsyncClient, name: str = "d") -> str:
    r = await client.post("/v1/monitoring/dashboards", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


@pytest.mark.asyncio
async def test_panel_create(live_app):
    client, _pool = live_app
    dash_id = await _make_dashboard(client, "d1")
    r = await client.post(
        f"/v1/monitoring/dashboards/{dash_id}/panels",
        json={
            "title": "tile1", "panel_type": "stat", "dsl": _DSL_METRICS,
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["title"] == "tile1"
    assert data["panel_type"] == "stat"
    assert data["dashboard_id"] == dash_id


@pytest.mark.asyncio
async def test_panel_update_dsl_and_gridpos(live_app):
    client, _pool = live_app
    dash_id = await _make_dashboard(client, "d2")
    r = await client.post(
        f"/v1/monitoring/dashboards/{dash_id}/panels",
        json={"title": "t", "panel_type": "stat", "dsl": _DSL_METRICS},
    )
    panel_id = r.json()["data"]["id"]
    r2 = await client.patch(
        f"/v1/monitoring/dashboards/{dash_id}/panels/{panel_id}",
        json={
            "dsl": {"target": "logs"},
            "grid_pos": {"x": 1, "y": 2, "w": 12, "h": 8},
        },
    )
    assert r2.status_code == 200, r2.text
    data = r2.json()["data"]
    assert data["dsl"] == {"target": "logs"}
    assert data["grid_pos"] == {"x": 1, "y": 2, "w": 12, "h": 8}


@pytest.mark.asyncio
async def test_panel_delete(live_app):
    client, _pool = live_app
    dash_id = await _make_dashboard(client, "d3")
    r = await client.post(
        f"/v1/monitoring/dashboards/{dash_id}/panels",
        json={"title": "t", "panel_type": "stat", "dsl": _DSL_METRICS},
    )
    panel_id = r.json()["data"]["id"]
    r2 = await client.delete(
        f"/v1/monitoring/dashboards/{dash_id}/panels/{panel_id}"
    )
    assert r2.status_code == 204
    r3 = await client.get(
        f"/v1/monitoring/dashboards/{dash_id}/panels/{panel_id}"
    )
    assert r3.status_code == 404


@pytest.mark.asyncio
async def test_panel_cascade_on_dashboard_hard_delete(live_app):
    """FK ON DELETE CASCADE — if a dashboard is hard-deleted, panels go too.

    Note: the HTTP DELETE endpoint does a SOFT delete; this test exercises the
    cascade directly via the raw table to prove the constraint is in place.
    """
    client, pool = live_app
    dash_id = await _make_dashboard(client, "d4")
    r = await client.post(
        f"/v1/monitoring/dashboards/{dash_id}/panels",
        json={"title": "t", "panel_type": "stat", "dsl": _DSL_METRICS},
    )
    panel_id = r.json()["data"]["id"]
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "05_monitoring"."10_fct_monitoring_dashboards" WHERE id = $1',
            dash_id,
        )
        row = await conn.fetchrow(
            'SELECT 1 FROM "05_monitoring"."11_fct_monitoring_panels" WHERE id = $1',
            panel_id,
        )
        assert row is None


@pytest.mark.asyncio
async def test_panel_invalid_type_rejected(live_app):
    client, _pool = live_app
    dash_id = await _make_dashboard(client, "d5")
    r = await client.post(
        f"/v1/monitoring/dashboards/{dash_id}/panels",
        json={"title": "t", "panel_type": "pie_chart", "dsl": _DSL_METRICS},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_panel_cross_dashboard_update_rejected(live_app):
    client, _pool = live_app
    d1 = await _make_dashboard(client, "d6a")
    d2 = await _make_dashboard(client, "d6b")
    r = await client.post(
        f"/v1/monitoring/dashboards/{d1}/panels",
        json={"title": "t", "panel_type": "stat", "dsl": _DSL_METRICS},
    )
    panel_id = r.json()["data"]["id"]
    # Try updating via wrong dashboard — must 404.
    r2 = await client.patch(
        f"/v1/monitoring/dashboards/{d2}/panels/{panel_id}",
        json={"title": "hijack"},
    )
    assert r2.status_code == 404

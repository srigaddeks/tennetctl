"""Tests for monitoring.escalation — on-call schedule + resolution (40-01 AC-2)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_oncall_module: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.08_escalation.oncall"
)
_core_id: Any = import_module("backend.01_core.id")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0808-0007-7000-0000-000000000001"
_WS_ID = "019e0808-0007-7000-0000-000000000002"
_USER_ID = "019e0808-0007-7000-0000-000000000003"
_USER_ID_2 = "019e0808-0007-7000-0000-000000000005"
_USER_ID_3 = "019e0808-0007-7000-0000-000000000006"
_SESSION_ID = "019e0808-0007-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID, "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID, "x-session-id": _SESSION_ID,
}


def _valid_create_schedule(
    name: str = "test-schedule",
    members: list[str] | None = None,
) -> dict[str, Any]:
    if members is None:
        members = [_USER_ID, _USER_ID_2, _USER_ID_3]
    return {
        "name": name,
        "description": "unit-test schedule",
        "timezone": "UTC",
        "rotation_period_seconds": 604800,  # 1 week
        "rotation_start": "2026-01-05T00:00:00Z",
        "members": members,
    }


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            '''DELETE FROM "05_monitoring"."20_dtl_monitoring_alert_escalation_state"
               WHERE policy_id IN (
                   SELECT id FROM "05_monitoring"."10_fct_monitoring_escalation_policies"
                   WHERE org_id=$1)''',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "05_monitoring"."10_fct_monitoring_escalation_policies" WHERE org_id=$1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "05_monitoring"."10_fct_monitoring_oncall_schedules" WHERE org_id=$1',
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
async def test_create_schedule(live_app):
    """AC-2: POST creates schedule + members."""
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/oncall-schedules",
        json=_valid_create_schedule("schedule-1"),
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["name"] == "schedule-1"
    assert len(data["members"]) == 3
    assert data["timezone"] == "UTC"
    assert data["rotation_period_seconds"] == 604800


@pytest.mark.asyncio
async def test_resolve_oncall_rotation(live_app):
    """AC-2: Rotation math: index = floor((elapsed) / period) % member_count."""
    client, _pool = live_app
    create_r = await client.post(
        "/v1/monitoring/oncall-schedules",
        json=_valid_create_schedule("rotation-test"),
    )
    assert create_r.status_code == 201
    data = create_r.json()["data"]

    # At 2026-01-05 (rotation_start), should be member 0 (user_id)
    rotation_start = datetime(2026, 1, 5, 0, 0, 0)
    members = data["members"]
    result = _oncall_module.resolve_oncall(data, members, rotation_start)
    assert result == _USER_ID

    # After 1 week (604800 seconds), should be member 1
    one_week_later = rotation_start + timedelta(seconds=604800)
    result = _oncall_module.resolve_oncall(data, members, one_week_later)
    assert result == _USER_ID_2

    # After 2 weeks, should be member 2
    two_weeks_later = rotation_start + timedelta(seconds=604800 * 2)
    result = _oncall_module.resolve_oncall(data, members, two_weeks_later)
    assert result == _USER_ID_3

    # After 3 weeks, should loop back to member 0
    three_weeks_later = rotation_start + timedelta(seconds=604800 * 3)
    result = _oncall_module.resolve_oncall(data, members, three_weeks_later)
    assert result == _USER_ID


@pytest.mark.asyncio
async def test_whoami_endpoint(live_app):
    """AC-2: GET /whoami returns current user + on_until."""
    client, _pool = live_app
    create_r = await client.post(
        "/v1/monitoring/oncall-schedules",
        json=_valid_create_schedule("whoami-test"),
    )
    assert create_r.status_code == 201
    schedule_id = create_r.json()["data"]["id"]

    whoami_r = await client.get(f"/v1/monitoring/oncall-schedules/{schedule_id}/whoami")
    assert whoami_r.status_code == 200, whoami_r.text
    data = whoami_r.json()["data"]
    assert "user_id" in data
    assert "user_email" in data
    assert "on_until" in data
    assert data["schedule_id"] == schedule_id


@pytest.mark.asyncio
async def test_list_schedules(live_app):
    """AC-2: GET lists schedules."""
    client, _pool = live_app
    for i in range(3):
        r = await client.post(
            "/v1/monitoring/oncall-schedules",
            json=_valid_create_schedule(f"list-test-{i}"),
        )
        assert r.status_code == 201

    list_r = await client.get("/v1/monitoring/oncall-schedules")
    assert list_r.status_code == 200
    data = list_r.json()
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_update_schedule_replaces_members(live_app):
    """AC-2: PATCH replaces member set entirely."""
    client, _pool = live_app
    create_r = await client.post(
        "/v1/monitoring/oncall-schedules",
        json=_valid_create_schedule("update-test"),
    )
    assert create_r.status_code == 201
    schedule_id = create_r.json()["data"]["id"]

    # Update with different members
    update_r = await client.patch(
        f"/v1/monitoring/oncall-schedules/{schedule_id}",
        json={"members": [_USER_ID_2, _USER_ID_3]},
    )
    assert update_r.status_code == 200
    updated = update_r.json()["data"]
    assert len(updated["members"]) == 2
    assert updated["members"][0]["user_id"] == _USER_ID_2
    assert updated["members"][1]["user_id"] == _USER_ID_3


@pytest.mark.asyncio
async def test_delete_schedule(live_app):
    """AC-2: DELETE soft-deletes."""
    client, _pool = live_app
    create_r = await client.post(
        "/v1/monitoring/oncall-schedules",
        json=_valid_create_schedule("delete-test"),
    )
    assert create_r.status_code == 201
    schedule_id = create_r.json()["data"]["id"]

    del_r = await client.delete(f"/v1/monitoring/oncall-schedules/{schedule_id}")
    assert del_r.status_code == 204

    # Verify soft-deleted
    list_r = await client.get("/v1/monitoring/oncall-schedules")
    ids = [s["id"] for s in list_r.json()["data"]]
    assert schedule_id not in ids

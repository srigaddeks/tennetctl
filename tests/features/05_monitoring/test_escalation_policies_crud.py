"""Tests for monitoring.escalation — escalation policy CRUD (40-01 AC-1)."""

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

_ORG_ID = "019e0808-0007-7000-0000-000000000001"
_WS_ID = "019e0808-0007-7000-0000-000000000002"
_USER_ID = "019e0808-0007-7000-0000-000000000003"
_SESSION_ID = "019e0808-0007-7000-0000-000000000004"
_OTHER_ORG = "019e0808-0007-7000-0000-0000000000aa"

_HDR = {
    "x-org-id": _ORG_ID, "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID, "x-session-id": _SESSION_ID,
}


def _valid_create_body(name: str = "test-policy") -> dict[str, Any]:
    return {
        "name": name,
        "description": "unit-test policy",
        "steps": [
            {
                "kind": "notify_user",
                "target_ref": {"user_id": _USER_ID},
                "priority": 2,
            },
            {
                "kind": "wait",
                "wait_seconds": 300,
            },
            {
                "kind": "notify_user",
                "target_ref": {"user_id": _USER_ID},
                "priority": 3,
            },
        ],
    }


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        for org in (_ORG_ID, _OTHER_ORG):
            # Delete escalation state, steps, then policies
            await conn.execute(
                '''DELETE FROM "05_monitoring"."20_dtl_monitoring_alert_escalation_state"
                   WHERE policy_id IN (
                       SELECT id FROM "05_monitoring"."10_fct_monitoring_escalation_policies"
                       WHERE org_id=$1)''',
                org,
            )
            await conn.execute(
                'DELETE FROM "05_monitoring"."10_fct_monitoring_escalation_policies" WHERE org_id=$1',
                org,
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
async def test_create_policy_happy_path(live_app):
    """AC-1: POST creates policy + steps with auto-assigned step_order."""
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/escalation-policies", json=_valid_create_body("alpha"),
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["name"] == "alpha"
    assert len(data["steps"]) == 3
    assert data["steps"][0]["step_order"] == 0
    assert data["steps"][0]["kind_code"] == "notify_user"
    assert data["steps"][1]["step_order"] == 1
    assert data["steps"][1]["kind_code"] == "wait"


@pytest.mark.asyncio
async def test_create_policy_duplicate_name_rejected(live_app):
    """AC-1: POST with existing name returns 409."""
    client, _pool = live_app
    body = _valid_create_body("dup-name")
    r1 = await client.post("/v1/monitoring/escalation-policies", json=body)
    assert r1.status_code == 201

    r2 = await client.post("/v1/monitoring/escalation-policies", json=body)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_get_policy(live_app):
    """AC-1: GET /id returns policy."""
    client, _pool = live_app
    create_r = await client.post(
        "/v1/monitoring/escalation-policies", json=_valid_create_body("get-test"),
    )
    assert create_r.status_code == 201
    policy_id = create_r.json()["data"]["id"]

    get_r = await client.get(f"/v1/monitoring/escalation-policies/{policy_id}")
    assert get_r.status_code == 200
    assert get_r.json()["data"]["id"] == policy_id


@pytest.mark.asyncio
async def test_list_policies(live_app):
    """AC-1: GET lists policies with pagination."""
    client, _pool = live_app
    # Create 3 policies
    for i in range(3):
        r = await client.post(
            "/v1/monitoring/escalation-policies",
            json=_valid_create_body(f"list-test-{i}"),
        )
        assert r.status_code == 201

    list_r = await client.get("/v1/monitoring/escalation-policies?offset=0&limit=10")
    assert list_r.status_code == 200
    data = list_r.json()
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_update_policy_replaces_steps(live_app):
    """AC-1: PATCH replaces step set entirely (immutable per step_order)."""
    client, _pool = live_app
    create_r = await client.post(
        "/v1/monitoring/escalation-policies", json=_valid_create_body("update-test"),
    )
    assert create_r.status_code == 201
    policy_id = create_r.json()["data"]["id"]

    # Update with 2 steps
    update_r = await client.patch(
        f"/v1/monitoring/escalation-policies/{policy_id}",
        json={
            "steps": [
                {
                    "kind": "notify_user",
                    "target_ref": {"user_id": _USER_ID},
                    "priority": 3,
                },
                {
                    "kind": "repeat",
                },
            ],
        },
    )
    assert update_r.status_code == 200
    updated_data = update_r.json()["data"]
    assert len(updated_data["steps"]) == 2
    assert updated_data["steps"][0]["kind_code"] == "notify_user"
    assert updated_data["steps"][1]["kind_code"] == "repeat"


@pytest.mark.asyncio
async def test_delete_policy(live_app):
    """AC-1: DELETE soft-deletes policy."""
    client, _pool = live_app
    create_r = await client.post(
        "/v1/monitoring/escalation-policies", json=_valid_create_body("delete-test"),
    )
    assert create_r.status_code == 201
    policy_id = create_r.json()["data"]["id"]

    del_r = await client.delete(f"/v1/monitoring/escalation-policies/{policy_id}")
    assert del_r.status_code == 204

    # Verify soft-deleted (should not appear in list)
    list_r = await client.get("/v1/monitoring/escalation-policies")
    assert list_r.status_code == 200
    ids = [p["id"] for p in list_r.json()["data"]]
    assert policy_id not in ids


@pytest.mark.asyncio
async def test_policy_active_filter(live_app):
    """AC-1: GET with is_active filter."""
    client, _pool = live_app
    # Create and toggle active
    create_r = await client.post(
        "/v1/monitoring/escalation-policies", json=_valid_create_body("active-filter"),
    )
    assert create_r.status_code == 201
    policy_id = create_r.json()["data"]["id"]

    # Deactivate
    update_r = await client.patch(
        f"/v1/monitoring/escalation-policies/{policy_id}",
        json={"is_active": False},
    )
    assert update_r.status_code == 200

    # List only active
    list_r = await client.get("/v1/monitoring/escalation-policies?is_active=true")
    assert list_r.status_code == 200
    ids = [p["id"] for p in list_r.json()["data"]]
    assert policy_id not in ids

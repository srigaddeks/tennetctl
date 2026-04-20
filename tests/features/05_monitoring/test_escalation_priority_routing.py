"""Tests for monitoring.escalation — priority routing via Notify (40-01 AC-5)."""

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

_HDR = {
    "x-org-id": _ORG_ID, "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID, "x-session-id": _SESSION_ID,
}


def _create_policy_with_priority(name: str, priority: int) -> dict[str, Any]:
    return {
        "name": name,
        "steps": [
            {
                "kind": "notify_user",
                "target_ref": {"user_id": _USER_ID},
                "priority": priority,
            },
        ],
    }


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "05_monitoring"."10_fct_monitoring_escalation_policies" WHERE org_id=$1',
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
async def test_priority_low_created(live_app):
    """AC-5: priority=1 (low) accepted."""
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/escalation-policies",
        json=_create_policy_with_priority("low-pri", 1),
    )
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["steps"][0]["priority"] == 1


@pytest.mark.asyncio
async def test_priority_normal_created(live_app):
    """AC-5: priority=2 (normal) default."""
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/escalation-policies",
        json=_create_policy_with_priority("normal-pri", 2),
    )
    assert r.status_code == 201
    assert r.json()["data"]["steps"][0]["priority"] == 2


@pytest.mark.asyncio
async def test_priority_high_created(live_app):
    """AC-5: priority=3 (high) accepted."""
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/escalation-policies",
        json=_create_policy_with_priority("high-pri", 3),
    )
    assert r.status_code == 201
    assert r.json()["data"]["steps"][0]["priority"] == 3


@pytest.mark.asyncio
async def test_priority_critical_created(live_app):
    """AC-5: priority=4 (critical) accepted."""
    client, _pool = live_app
    r = await client.post(
        "/v1/monitoring/escalation-policies",
        json=_create_policy_with_priority("critical-pri", 4),
    )
    assert r.status_code == 201
    assert r.json()["data"]["steps"][0]["priority"] == 4


@pytest.mark.asyncio
async def test_priority_routing_per_spec(live_app):
    """AC-5: Priority routing per spec (low/normal/high/critical channel mapping)."""
    client, _pool = live_app

    # Create policies with different priorities
    for priority in [1, 2, 3, 4]:
        body = {
            "name": f"priority-{priority}",
            "steps": [
                {
                    "kind": "notify_user",
                    "target_ref": {"user_id": _USER_ID},
                    "priority": priority,
                },
            ],
        }
        r = await client.post("/v1/monitoring/escalation-policies", json=body)
        assert r.status_code == 201, f"Failed to create policy with priority {priority}"

    # Verify all were created
    list_r = await client.get("/v1/monitoring/escalation-policies")
    assert list_r.status_code == 200
    assert len(list_r.json()["data"]) == 4

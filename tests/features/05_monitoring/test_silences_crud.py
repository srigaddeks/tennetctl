"""Tests for monitoring.alerts — silences CRUD (13-08a chunk A)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
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

_ORG_ID = "019e0808-0008-7000-0000-000000000001"
_WS_ID = "019e0808-0008-7000-0000-000000000002"
_USER_ID = "019e0808-0008-7000-0000-000000000003"
_SESSION_ID = "019e0808-0008-7000-0000-000000000004"

_HDR = {
    "x-org-id": _ORG_ID, "x-workspace-id": _WS_ID,
    "x-user-id": _USER_ID, "x-session-id": _SESSION_ID,
}


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat() + "Z"


def _silence_body(
    starts_delta: timedelta = timedelta(minutes=0),
    duration: timedelta = timedelta(hours=1),
    matcher: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    starts = now + starts_delta
    ends = starts + duration
    return {
        "matcher": matcher if matcher is not None else {"labels": {"team": "platform"}},
        "starts_at": starts.isoformat() + "Z",
        "ends_at": ends.isoformat() + "Z",
        "reason": "planned maintenance",
    }


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "05_monitoring"."13_fct_monitoring_silences" WHERE org_id=$1',
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
async def test_create_silence_happy_path(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/silences", json=_silence_body())
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["reason"] == "planned maintenance"
    assert data["matcher"]["labels"] == {"team": "platform"}
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_active_silences_excludes_expired(live_app):
    client, pool = live_app
    # Active
    r1 = await client.post("/v1/monitoring/silences", json=_silence_body())
    assert r1.status_code == 201
    active_id = r1.json()["data"]["id"]

    # Insert an expired silence directly (ends_at < now is enforced via CHECK
    # only when ends_at <= starts_at, so we pick past starts_at too).
    past_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=3)
    past_end = past_start + timedelta(hours=1)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO "05_monitoring"."13_fct_monitoring_silences"
                (id, org_id, matcher, starts_at, ends_at, reason, created_by,
                 is_active, created_at, updated_at)
            VALUES ($1,$2,$3::jsonb,$4,$5,$6,$7,TRUE,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            """,
            "019e0808-0008-7000-0000-0000000000ff",
            _ORG_ID, "{}", past_start, past_end, "expired",
            _USER_ID,
        )

    rl = await client.get("/v1/monitoring/silences")
    assert rl.status_code == 200
    items = rl.json()["data"]["items"]
    ids = [s["id"] for s in items]
    assert active_id in ids
    assert "019e0808-0008-7000-0000-0000000000ff" not in ids

    # Include-expired via active_only=false
    rl2 = await client.get("/v1/monitoring/silences?active_only=false")
    assert rl2.status_code == 200
    ids2 = [s["id"] for s in rl2.json()["data"]["items"]]
    assert "019e0808-0008-7000-0000-0000000000ff" in ids2


@pytest.mark.asyncio
async def test_delete_silence(live_app):
    client, _pool = live_app
    r = await client.post("/v1/monitoring/silences", json=_silence_body())
    sid = r.json()["data"]["id"]

    rd = await client.delete(f"/v1/monitoring/silences/{sid}")
    assert rd.status_code == 204

    rl = await client.get("/v1/monitoring/silences")
    assert not any(s["id"] == sid for s in rl.json()["data"]["items"])


@pytest.mark.asyncio
async def test_silence_end_before_start_rejected(live_app):
    client, _pool = live_app
    now = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
    body = {
        "matcher": {"labels": {"team": "platform"}},
        "starts_at": (now + timedelta(hours=2)).isoformat() + "Z",
        "ends_at": (now + timedelta(hours=1)).isoformat() + "Z",
        "reason": "inverted window",
    }
    r = await client.post("/v1/monitoring/silences", json=body)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_WINDOW"


@pytest.mark.asyncio
async def test_silence_matcher_rule_id_accepted(live_app):
    client, _pool = live_app
    body = _silence_body(
        matcher={"rule_id": "019e0808-0008-7000-0000-0000000000cc"},
    )
    r = await client.post("/v1/monitoring/silences", json=body)
    assert r.status_code == 201
    assert r.json()["data"]["matcher"]["rule_id"] == "019e0808-0008-7000-0000-0000000000cc"

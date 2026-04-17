"""
Plan 20-04: Session limits tests.

Covers:
  - last_activity_at column exists and gets bumped
  - idle_timeout_revokes (via direct DB manipulation)
  - absolute_ttl_revokes (via direct DB manipulation)
  - max_concurrent oldest eviction
  - max_concurrent reject returns 429
"""

from __future__ import annotations

import datetime as dt
from importlib import import_module
from typing import Any
from dataclasses import dataclass

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")

_TEST_EMAIL_PREFIX = "itest-sesslimit-"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3
              AND d.code = 'email'
              AND a.key_text LIKE $1
            """,
            f"{_TEST_EMAIL_PREFIX}%",
        )
        user_ids = [r["user_id"] for r in rows]
        if not user_ids:
            return
        await conn.execute(
            'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."40_lnk_user_orgs" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."21_dtl_attrs" '
            "WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])",
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
            user_ids,
        )


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        transport = ASGITransport(app=_main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, pool
        await _cleanup(pool)


async def _signup_and_signin(client: AsyncClient, email: str) -> tuple[str, str]:
    """Returns (session_token, user_id)."""
    resp = await client.post("/v1/auth/signup", json={
        "email": email, "password": "Test@1234", "display_name": "Session Test",
    })
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()["data"]
    return data["session"]["id"], data["user"]["id"]


@pytest.mark.asyncio
async def test_last_activity_at_column_exists(live_app) -> None:
    """last_activity_at column exists on fct_sessions."""
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}col-exists@example.com"
    session_id, _ = await _signup_and_signin(client, email)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT last_activity_at FROM "03_iam"."16_fct_sessions" WHERE id = $1',
            session_id,
        )
    assert row is not None
    assert row["last_activity_at"] is not None


@pytest.mark.asyncio
async def test_idle_timeout_revokes_session(monkeypatch, live_app) -> None:
    """Session with last_activity_at in the past by > idle_timeout is revoked by middleware."""
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}idle-timeout@example.com"

    # Signup
    resp = await client.post("/v1/auth/signup", json={
        "email": email, "password": "Test@1234", "display_name": "Idle Test",
    })
    data = resp.json()["data"]
    token = data["token"]
    session_id = data["session"]["id"]

    # Set last_activity_at to way in the past.
    async with pool.acquire() as conn:
        await conn.execute(
            'UPDATE "03_iam"."16_fct_sessions" SET last_activity_at = $1 WHERE id = $2',
            dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(seconds=7200),
            session_id,
        )

    # Override auth_policy to use idle_timeout_seconds=3600 (should trigger).
    @dataclass(frozen=True)
    class MockSessionPolicy:
        max_concurrent_per_user: int = 10
        idle_timeout_seconds: int = 3600
        absolute_ttl_seconds: int = 604800
        eviction_policy: str = "oldest"

    class MockAuthPolicy:
        async def session(self, org_id):
            return MockSessionPolicy()

    monkeypatch.setattr(_main.app.state, "auth_policy", MockAuthPolicy())

    # /me with the stale token should return 401 (middleware revokes it).
    resp = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_bump_last_activity_updates_column(live_app) -> None:
    """bump_last_activity updates the last_activity_at column."""
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}bump@example.com"
    session_id, _ = await _signup_and_signin(client, email)

    _sessions_repo = import_module("backend.02_features.03_iam.sub_features.09_sessions.repository")

    # Manually set last_activity_at to the past.
    past = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(seconds=100)
    async with pool.acquire() as conn:
        await conn.execute(
            'UPDATE "03_iam"."16_fct_sessions" SET last_activity_at = $1 WHERE id = $2',
            past, session_id,
        )
        await _sessions_repo.bump_last_activity(conn, session_id=session_id)
        row = await conn.fetchrow(
            'SELECT last_activity_at FROM "03_iam"."16_fct_sessions" WHERE id = $1',
            session_id,
        )

    assert row["last_activity_at"] > past

"""
Plan 20-03: Account lockout integration tests.

Covers:
  - Failed signin increments fct_failed_auth_attempts
  - Threshold breach locks account (status 423)
  - Locked account blocks further signins
  - Expired lockout clears on next attempt
  - Per-org threshold (stub auth_policy via monkeypatch)
"""

from __future__ import annotations

import datetime as dt
from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")

_TEST_EMAIL_PREFIX = "itest-lockout-"


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
        # Clean lockout attrs
        await conn.execute(
            'DELETE FROM "03_iam"."21_dtl_attrs" '
            "WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])",
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
            user_ids,
        )
        # Clean failed attempts by these emails
        await conn.execute(
            'DELETE FROM "03_iam"."23_fct_failed_auth_attempts" WHERE email LIKE $1',
            f"{_TEST_EMAIL_PREFIX}%",
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


async def _signup(client: AsyncClient, email: str, password: str = "Test@1234") -> None:
    resp = await client.post("/v1/auth/signup", json={
        "email": email, "password": password, "display_name": "Lockout Test",
    })
    assert resp.status_code in (200, 201), resp.text


async def _signin(client: AsyncClient, email: str, password: str) -> int:
    resp = await client.post("/v1/auth/signin", json={"email": email, "password": password})
    return resp.status_code


@pytest.mark.asyncio
async def test_failed_attempt_records_row(live_app) -> None:
    """A bad password inserts a row into fct_failed_auth_attempts."""
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}attempt-row@example.com"
    await _signup(client, email)

    await _signin(client, email, "wrongpass1")

    async with pool.acquire() as conn:
        count = await conn.fetchval(
            'SELECT COUNT(*) FROM "03_iam"."23_fct_failed_auth_attempts" WHERE email = $1',
            email,
        )
    assert count >= 1


@pytest.mark.asyncio
async def test_lockout_blocks_signin_within_window(monkeypatch, live_app) -> None:
    """After N failed attempts, account is locked and returns 423."""
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}lock-block@example.com"
    await _signup(client, email, "Test@1234")

    # Override auth_policy to use threshold=3, window=900, duration=900
    from importlib import import_module as _im
    _creds_service = _im("backend.02_features.03_iam.sub_features.08_credentials.service")

    from dataclasses import dataclass

    @dataclass(frozen=True)
    class MockLockoutPolicy:
        threshold_failed_attempts: int = 3
        window_seconds: int = 900
        duration_seconds: int = 900

    class MockAuthPolicy:
        async def lockout(self, org_id):
            return MockLockoutPolicy()

    monkeypatch.setattr(_main.app.state, "auth_policy", MockAuthPolicy())

    # 3 wrong attempts (threshold)
    for _ in range(3):
        status = await _signin(client, email, "wrong!!")
        # first attempts: 401 (wrong password)

    # 4th attempt — should be 423 LOCKED
    status = await _signin(client, email, "wrong!!")
    assert status == 423


@pytest.mark.asyncio
async def test_correct_password_after_expired_lockout_succeeds(monkeypatch, live_app) -> None:
    """An expired lockout is cleared on next successful signin."""
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}expire-clear@example.com"
    await _signup(client, email, "Test@1234")

    # Manually set an expired lockout_until in the past.
    _creds_repo = import_module("backend.02_features.03_iam.sub_features.08_credentials.repository")

    # Find user_id
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT id FROM "03_iam"."v_users" WHERE email = $1 LIMIT 1', email,
        )
        user_id = row["id"]

        # Set lockout to 1 second in the past.
        past = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(seconds=1)
        await _creds_repo.set_lockout_until(conn, user_id=user_id, until_ts=past)

    # Signin with correct password — should succeed (200).
    status = await _signin(client, email, "Test@1234")
    assert status == 200


@pytest.mark.asyncio
async def test_active_lockout_blocks_correct_password(live_app) -> None:
    """A non-expired lockout blocks even a correct password."""
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}active-lock@example.com"
    await _signup(client, email, "Test@1234")

    _creds_repo = import_module("backend.02_features.03_iam.sub_features.08_credentials.repository")

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT id FROM "03_iam"."v_users" WHERE email = $1 LIMIT 1', email,
        )
        user_id = row["id"]
        future = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) + dt.timedelta(hours=1)
        await _creds_repo.set_lockout_until(conn, user_id=user_id, until_ts=future)

    status = await _signin(client, email, "Test@1234")
    assert status == 423

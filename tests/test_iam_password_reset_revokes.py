"""
Plan 20-05: Password reset revokes all active sessions.

AC-3: Given user U has N active sessions, when U completes a password reset,
then all N sessions are revoked in the same tx as the password update, and
iam.password_reset.completed fires once.
"""

from __future__ import annotations

import datetime as dt
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")

_TEST_EMAIL_PREFIX = "itest-pwrevoke-"


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
            'DELETE FROM "03_iam"."27_fct_iam_password_reset_tokens" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
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


@pytest.mark.asyncio
async def test_password_reset_revokes_all_sessions(live_app) -> None:
    """After password reset, all prior sessions are revoked."""
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}revoke-all@example.com"

    # Sign up
    resp = await client.post("/v1/auth/signup", json={
        "email": email, "password": "Test@1234", "display_name": "PW Revoke All",
    })
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()["data"]
    user_id = data["user"]["id"]
    first_session_id = data["session"]["id"]

    # Create 2 more sessions by signing in again
    for _ in range(2):
        r = await client.post("/v1/auth/signin", json={"email": email, "password": "Test@1234"})
        assert r.status_code == 200, r.text

    # Verify 3 active sessions exist
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            'SELECT COUNT(*) FROM "03_iam"."16_fct_sessions" '
            'WHERE user_id = $1 AND revoked_at IS NULL AND deleted_at IS NULL AND expires_at > CURRENT_TIMESTAMP',
            user_id,
        )
    assert count == 3, f"Expected 3 active sessions, got {count}"

    # Get a raw reset token directly from DB (simulating request_reset)
    _pw_reset_svc = import_module("backend.02_features.03_iam.sub_features.14_password_reset.service")
    _pw_reset_repo = import_module("backend.02_features.03_iam.sub_features.14_password_reset.repository")
    vault = _main.app.state.vault

    import secrets
    import hashlib
    import hmac as _hmac

    # Get signing key
    raw_token = secrets.token_urlsafe(32)
    async with pool.acquire() as conn:
        signing_key = await _pw_reset_svc._signing_key_bytes(vault)
        token_hash = _pw_reset_svc._hash_token(raw_token, signing_key)
        expires_at = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) + dt.timedelta(minutes=15)

        _core_id = import_module("backend.01_core.id")
        await _pw_reset_repo.create_token(
            conn,
            token_id=_core_id.uuid7(),
            user_id=user_id,
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=None,
        )

    t0 = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    # Complete the reset
    resp = await client.post("/v1/auth/password-reset/complete", json={
        "token": raw_token,
        "new_password": "NewPass@5678",
    })
    assert resp.status_code in (200, 201), resp.text

    # All prior 3 sessions must now be revoked
    async with pool.acquire() as conn:
        active = await conn.fetchval(
            'SELECT COUNT(*) FROM "03_iam"."16_fct_sessions" '
            'WHERE user_id = $1 AND revoked_at IS NULL AND deleted_at IS NULL AND expires_at > CURRENT_TIMESTAMP',
            user_id,
        )
    # Only the new session (from complete_reset) should be active
    assert active == 1, f"Expected 1 active session (new), got {active}"

    # iam.password_reset.completed should be in audit
    async with pool.acquire() as conn:
        audit_row = await conn.fetchrow(
            'SELECT event_key, outcome FROM "04_audit"."60_evt_audit" '
            'WHERE event_key = $1 AND created_at >= $2 ORDER BY created_at DESC LIMIT 1',
            "iam.password_reset.completed", t0,
        )
    assert audit_row is not None, "iam.password_reset.completed not found in audit"
    assert audit_row["outcome"] == "success"

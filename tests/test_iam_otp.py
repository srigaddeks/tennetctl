"""
Integration tests for iam.otp — Plan 12-02.

Covers: email OTP request (unknown → silent 200, known → 200),
verify (invalid code → 401, too many attempts → 401, valid → session),
TOTP setup + verify happy path.
"""

from __future__ import annotations

import pyotp
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_users_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_otp_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.12_otp.repository"
)
_otp_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.12_otp.service"
)
_core_id: Any = import_module("backend.01_core.id")
_ctx_mod: Any = import_module("backend.01_catalog.context")

_TEST_EMAIL_PREFIX = "itest-otp-"


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
        await conn.execute(
            'DELETE FROM "03_iam"."23_fct_iam_otp_codes" WHERE email LIKE $1',
            f"{_TEST_EMAIL_PREFIX}%",
        )
        if not user_ids:
            return
        await conn.execute(
            'DELETE FROM "03_iam"."24_fct_iam_totp_credentials" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."40_lnk_user_orgs" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])',
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
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac, pool
        finally:
            await _cleanup(pool)


def _sys_ctx(pool: Any, conn: Any) -> Any:
    return _ctx_mod.NodeContext(
        audit_category="setup",
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        conn=conn,
        extras={"pool": pool},
    )


async def _make_user(pool: Any, suffix: str = "user") -> dict:
    async with pool.acquire() as conn:
        ctx = _sys_ctx(pool, conn)
        return await _users_service.create_user(
            pool, conn, ctx,
            email=f"{_TEST_EMAIL_PREFIX}{suffix}@example.com",
            display_name="OTP Test User",
            account_type="email_password",
        )


async def _insert_otp(pool: Any, *, user_id: str, email: str, code: str, attempts: int = 0, expired: bool = False) -> str:
    code_hash = _otp_service._hash_code(code)
    if expired:
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=10)
    else:
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=5)
    async with pool.acquire() as conn:
        await _otp_repo.create_otp_code(
            conn,
            code_id=_core_id.uuid7(),
            user_id=user_id,
            email=email,
            code_hash=code_hash,
            expires_at=expires_at,
        )
        if attempts > 0:
            for _ in range(attempts):
                await _otp_repo.increment_otp_attempts(conn, await conn.fetchval(
                    'SELECT id FROM "03_iam"."23_fct_iam_otp_codes" WHERE email=$1 ORDER BY created_at DESC LIMIT 1',
                    email,
                ))
    return code


# ─── Email OTP tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_otp_request_unknown_email_returns_200(live_app):
    """Unknown email must silently return 200."""
    client, _pool = live_app
    r = await client.post("/v1/auth/otp/request", json={"email": "nobody-xyz-99999@example.com"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_otp_request_known_email_returns_200(live_app):
    client, pool = live_app
    user = await _make_user(pool, "req1")
    r = await client.post("/v1/auth/otp/request", json={"email": user["email"]})
    assert r.status_code == 200
    assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_otp_verify_invalid_code_returns_401(live_app):
    client, pool = live_app
    user = await _make_user(pool, "inv1")
    await _insert_otp(pool, user_id=user["id"], email=user["email"], code="123456")
    r = await client.post("/v1/auth/otp/verify", json={"email": user["email"], "code": "000000"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CODE"


@pytest.mark.asyncio
async def test_otp_verify_too_many_attempts_returns_401(live_app):
    client, pool = live_app
    user = await _make_user(pool, "max1")
    await _insert_otp(pool, user_id=user["id"], email=user["email"], code="111111", attempts=3)
    r = await client.post("/v1/auth/otp/verify", json={"email": user["email"], "code": "111111"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "MAX_ATTEMPTS"


@pytest.mark.asyncio
async def test_otp_verify_valid_code_returns_session(live_app):
    client, pool = live_app
    user = await _make_user(pool, "ok1")
    code = "654321"
    await _insert_otp(pool, user_id=user["id"], email=user["email"], code=code)
    r = await client.post("/v1/auth/otp/verify", json={"email": user["email"], "code": code})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "token" in data["data"]
    assert "session" in data["data"]


# ─── TOTP tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_totp_setup_and_verify(live_app):
    """Setup TOTP credential, then verify a valid code."""
    client, pool = live_app
    user = await _make_user(pool, "totp1")
    vault = _main.app.state.vault

    # Setup TOTP directly via service (requires auth in route)
    async with pool.acquire() as conn:
        ctx = _sys_ctx(pool, conn)
        result = await _otp_service.setup_totp(
            pool, conn, ctx,
            user_id=user["id"],
            device_name="pytest-authenticator",
            vault_client=vault,
        )

    cred_id = result["credential_id"]
    uri = result["otpauth_uri"]
    assert cred_id
    assert "otpauth://" in uri

    # Extract secret from URI to generate valid code
    secret = pyotp.parse_uri(uri).secret
    code = pyotp.TOTP(secret).now()

    r = await client.post("/v1/auth/totp/verify", json={"credential_id": cred_id, "code": code})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "token" in data["data"]


@pytest.mark.asyncio
async def test_totp_verify_wrong_code_returns_401(live_app):
    client, pool = live_app
    user = await _make_user(pool, "totp2")
    vault = _main.app.state.vault

    async with pool.acquire() as conn:
        ctx = _sys_ctx(pool, conn)
        result = await _otp_service.setup_totp(
            pool, conn, ctx,
            user_id=user["id"],
            device_name="pytest-bad",
            vault_client=vault,
        )

    r = await client.post("/v1/auth/totp/verify", json={"credential_id": result["credential_id"], "code": "000000"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CODE"

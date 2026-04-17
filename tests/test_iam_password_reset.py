"""
Integration tests for iam.password_reset — Plan 12-04.

Covers: request (unknown → 200, known → 200), complete (invalid → 401,
expired → 401, valid → 200 + session + new password works).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_users_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_credentials_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.08_credentials.service"
)
_pr_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.14_password_reset.repository"
)
_pr_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.14_password_reset.service"
)
_core_id: Any = import_module("backend.01_core.id")
_ctx_mod: Any = import_module("backend.01_catalog.context")

_TEST_PREFIX = "itest-pr-"


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
            f"{_TEST_PREFIX}%",
        )
        user_ids = [r["user_id"] for r in rows]
        await conn.execute(
            'DELETE FROM "03_iam"."27_fct_iam_password_reset_tokens" WHERE email LIKE $1',
            f"{_TEST_PREFIX}%",
        )
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


async def _make_user(pool: Any, suffix: str = "u1") -> dict:
    async with pool.acquire() as conn:
        ctx = _sys_ctx(pool, conn)
        return await _users_service.create_user(
            pool, conn, ctx,
            email=f"{_TEST_PREFIX}{suffix}@example.com",
            display_name="Reset Test User",
            account_type="email_password",
        )


async def _insert_token(pool: Any, *, user_id: str, email: str, code: str, expired: bool = False) -> str:
    vault = _main.app.state.vault
    signing_key = await _pr_service._signing_key_bytes(vault)
    raw_token = secrets.token_urlsafe(32)
    token_hash = _pr_service._hash_token(raw_token, signing_key)
    if expired:
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5)
    else:
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=_pr_service._TOKEN_TTL_MINUTES)
    async with pool.acquire() as conn:
        await _pr_repo.create_token(
            conn,
            token_id=_core_id.uuid7(),
            user_id=user_id,
            email=email,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    return raw_token


@pytest.mark.asyncio
async def test_request_unknown_email_returns_200(live_app):
    """Unknown email must return 200 without revealing user non-existence."""
    client, _pool = live_app
    r = await client.post("/v1/auth/password-reset/request", json={"email": "nobody-xyz-pr@example.com"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_request_known_email_returns_200(live_app):
    client, pool = live_app
    user = await _make_user(pool, "req1")
    r = await client.post("/v1/auth/password-reset/request", json={"email": user["email"]})
    assert r.status_code == 200
    assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_complete_invalid_token_returns_401(live_app):
    client, _pool = live_app
    r = await client.post("/v1/auth/password-reset/complete", json={"token": "bogus-token", "new_password": "NewPass123!"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_complete_expired_token_returns_401(live_app):
    client, pool = live_app
    user = await _make_user(pool, "exp1")
    raw_token = await _insert_token(pool, user_id=user["id"], email=user["email"], code="", expired=True)
    r = await client.post("/v1/auth/password-reset/complete", json={"token": raw_token, "new_password": "NewPass123!"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_complete_weak_password_returns_422(live_app):
    client, pool = live_app
    user = await _make_user(pool, "weak1")
    raw_token = await _insert_token(pool, user_id=user["id"], email=user["email"], code="")
    r = await client.post("/v1/auth/password-reset/complete", json={"token": raw_token, "new_password": "short"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "WEAK_PASSWORD"


@pytest.mark.asyncio
async def test_complete_valid_token_resets_password_and_returns_session(live_app):
    """Valid token → password updated, session returned."""
    client, pool = live_app
    user = await _make_user(pool, "ok1")
    vault = _main.app.state.vault

    # Set initial password
    async with pool.acquire() as conn:
        await _credentials_service.set_password(conn, vault_client=vault, user_id=user["id"], value="OldPass123!")

    raw_token = await _insert_token(pool, user_id=user["id"], email=user["email"], code="")
    r = await client.post("/v1/auth/password-reset/complete", json={"token": raw_token, "new_password": "NewPass123!"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "token" in data["data"]
    assert "session" in data["data"]

    # Verify old password no longer works
    async with pool.acquire() as conn:
        ok_old = await _credentials_service.verify_password(conn, vault_client=vault, user_id=user["id"], value="OldPass123!")
        ok_new = await _credentials_service.verify_password(conn, vault_client=vault, user_id=user["id"], value="NewPass123!")
    assert not ok_old
    assert ok_new


@pytest.mark.asyncio
async def test_complete_same_token_twice_fails(live_app):
    """Second use of same reset token → 401."""
    client, pool = live_app
    user = await _make_user(pool, "dup1")
    raw_token = await _insert_token(pool, user_id=user["id"], email=user["email"], code="")

    r1 = await client.post("/v1/auth/password-reset/complete", json={"token": raw_token, "new_password": "NewPass123!"})
    assert r1.status_code == 200

    r2 = await client.post("/v1/auth/password-reset/complete", json={"token": raw_token, "new_password": "AnotherPass!"})
    assert r2.status_code == 401
    assert r2.json()["error"]["code"] == "INVALID_TOKEN"

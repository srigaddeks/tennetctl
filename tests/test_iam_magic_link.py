"""
Integration tests for iam.magic_link — Plan 12-01.

Covers: request (user not found → silent, user found → 200),
consume (invalid token → 401, expired → 401, valid → 200 session),
consume same token twice → 401.
"""

from __future__ import annotations

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
_ml_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.11_magic_link.service"
)
_ml_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.11_magic_link.repository"
)
_core_id: Any = import_module("backend.01_core.id")
_ctx_mod: Any = import_module("backend.01_catalog.context")

_TEST_EMAIL_PREFIX = "itest-ml-"


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
            """
            DELETE FROM "04_audit"."60_evt_audit"
            WHERE event_key LIKE 'iam.magic_link.%'
            """,
        )
        if not user_ids:
            return
        await conn.execute(
            'DELETE FROM "03_iam"."19_fct_iam_magic_link_tokens" WHERE user_id = ANY($1::text[])',
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


async def _make_ml_user(pool: Any) -> dict:
    async with pool.acquire() as conn:
        ctx = _sys_ctx(pool, conn)
        return await _users_service.create_user(
            pool, conn, ctx,
            email=f"{_TEST_EMAIL_PREFIX}user@example.com",
            display_name="ML User",
            account_type="magic_link",
        )


async def _insert_token(pool: Any, *, user_id: str, email: str, expires_at: datetime) -> str:
    vault = _main.app.state.vault
    signing_key = await _ml_service._signing_key_bytes(vault)
    raw_token = secrets.token_urlsafe(32)
    token_hash = _ml_service._hash_token(raw_token, signing_key)
    async with pool.acquire() as conn:
        await _ml_repo.create_token(
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
    r = await client.post("/v1/auth/magic-link/request", json={
        "email": "nobody-nonexistent-12345@example.com",
    })
    assert r.status_code == 200
    assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_request_known_email_returns_200(live_app):
    client, pool = live_app
    user = await _make_ml_user(pool)
    r = await client.post("/v1/auth/magic-link/request", json={"email": user["email"]})
    assert r.status_code == 200
    assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_consume_invalid_token_returns_401(live_app):
    client, _pool = live_app
    r = await client.post("/v1/auth/magic-link/consume", json={"token": "bogus-token"})
    assert r.status_code == 401
    assert r.json()["ok"] is False


@pytest.mark.asyncio
async def test_consume_valid_token_returns_session(live_app):
    client, pool = live_app
    user = await _make_ml_user(pool)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10)
    raw_token = await _insert_token(pool, user_id=user["id"], email=user["email"], expires_at=expires_at)

    r = await client.post("/v1/auth/magic-link/consume", json={"token": raw_token})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "token" in data["data"]
    assert "session" in data["data"]


@pytest.mark.asyncio
async def test_consume_same_token_twice_fails(live_app):
    """Second consume of same token → 401 TOKEN_ALREADY_USED."""
    client, pool = live_app
    user = await _make_ml_user(pool)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10)
    raw_token = await _insert_token(pool, user_id=user["id"], email=user["email"], expires_at=expires_at)

    r1 = await client.post("/v1/auth/magic-link/consume", json={"token": raw_token})
    assert r1.status_code == 200

    r2 = await client.post("/v1/auth/magic-link/consume", json={"token": raw_token})
    assert r2.status_code == 401
    assert r2.json()["error"]["code"] == "TOKEN_ALREADY_USED"


@pytest.mark.asyncio
async def test_consume_expired_token_returns_401(live_app):
    client, pool = live_app
    user = await _make_ml_user(pool)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5)
    raw_token = await _insert_token(pool, user_id=user["id"], email=user["email"], expires_at=expires_at)

    r = await client.post("/v1/auth/magic-link/consume", json={"token": raw_token})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "TOKEN_EXPIRED"

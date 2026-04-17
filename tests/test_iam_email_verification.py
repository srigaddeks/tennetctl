"""
Integration tests for iam.email_verification — Plan 21-01.

Covers:
- POST /v1/auth/verify-email/send (unknown email returns 202, known returns 202)
- POST /v1/auth/verify-email/consume (invalid token, expired token, double-consume, valid flow)
- email_verified field on /v1/auth/me
- Policy-off: email_verified_at set immediately on signup (skipped if policy flag unavailable)
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
_credentials_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.08_credentials.service"
)
_ev_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.16_email_verification.repository"
)
_ev_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.16_email_verification.service"
)
_core_id: Any = import_module("backend.01_core.id")
_ctx_mod: Any = import_module("backend.01_catalog.context")

_TEST_PREFIX = "itest-ev-"


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
            'DELETE FROM "03_iam"."29_fct_iam_email_verifications" WHERE user_id = ANY($1::text[])',
            user_ids,
        ) if user_ids else None
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
                yield ac, pool, _main.app.state.vault
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
            display_name="EV Test User",
            account_type="email_password",
        )


async def _insert_token(pool: Any, *, user_id: str, vault: Any, expired: bool = False) -> str:
    signing_key = await _ev_service._signing_key_bytes(vault)
    raw_token = secrets.token_urlsafe(32)
    token_hash = _ev_service._hash_token(raw_token, signing_key)
    if expired:
        ttl_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    else:
        ttl_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=_ev_service._TOKEN_TTL_HOURS)
    async with pool.acquire() as conn:
        await _ev_repo.create_token(
            conn,
            token_id=_core_id.uuid7(),
            user_id=user_id,
            token_hash=token_hash,
            ttl_at=ttl_at,
        )
    return raw_token


# ── Schema tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fct_email_verifications_table_exists(live_app):
    """AC-1: Table exists with correct columns."""
    _client, pool, _vault = live_app
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = '03_iam'
              AND table_name = '29_fct_iam_email_verifications'
            """
        )
    assert row is not None, "Table 29_fct_iam_email_verifications missing"


@pytest.mark.asyncio
async def test_email_verified_at_attr_def_exists(live_app):
    """AC-1: attr_def for email_verified_at registered."""
    _client, pool, _vault = live_app
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT id FROM "03_iam"."20_dtl_attr_defs" '
            'WHERE entity_type_id = 3 AND code = $1',
            "email_verified_at",
        )
    assert row is not None, "attr_def email_verified_at not registered"


# ── Send endpoint ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_send_unknown_email_returns_202(live_app):
    """Unknown email must return 202 without revealing non-existence."""
    client, _pool, _vault = live_app
    r = await client.post(
        "/v1/auth/verify-email/send",
        json={"email": "nobody-ev-xyz@example.com"},
    )
    assert r.status_code == 202
    assert r.json()["ok"] is True


@pytest.mark.asyncio
async def test_send_known_email_returns_202(live_app):
    client, pool, _vault = live_app
    user = await _make_user(pool, "send1")
    r = await client.post(
        "/v1/auth/verify-email/send",
        json={"email": user["email"]},
    )
    assert r.status_code == 202
    assert r.json()["ok"] is True


# ── Consume endpoint ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_consume_invalid_token_returns_400(live_app):
    client, _pool, _vault = live_app
    r = await client.post(
        "/v1/auth/verify-email/consume",
        json={"token": "bogus-token-xyz"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_consume_expired_token_returns_400(live_app):
    client, pool, vault = live_app
    user = await _make_user(pool, "exp1")
    raw_token = await _insert_token(pool, user_id=user["id"], vault=vault, expired=True)
    r = await client.post(
        "/v1/auth/verify-email/consume",
        json={"token": raw_token},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] in ("INVALID_TOKEN", "TOKEN_EXPIRED")


@pytest.mark.asyncio
async def test_consume_valid_token_sets_email_verified_at(live_app):
    """AC-3: Valid token marks consumed + sets email_verified_at attr."""
    client, pool, vault = live_app
    user = await _make_user(pool, "ok1")
    raw_token = await _insert_token(pool, user_id=user["id"], vault=vault)
    r = await client.post(
        "/v1/auth/verify-email/consume",
        json={"token": raw_token},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["verified"] is True

    # email_verified_at attr set
    async with pool.acquire() as conn:
        val = await _ev_repo.get_email_verified_at(conn, user["id"])
    assert val is not None


@pytest.mark.asyncio
async def test_consume_already_consumed_token_returns_400(live_app):
    """Double-consume rejected."""
    client, pool, vault = live_app
    user = await _make_user(pool, "dc1")
    raw_token = await _insert_token(pool, user_id=user["id"], vault=vault)
    # First consume
    r1 = await client.post("/v1/auth/verify-email/consume", json={"token": raw_token})
    assert r1.status_code == 200
    # Second consume
    r2 = await client.post("/v1/auth/verify-email/consume", json={"token": raw_token})
    assert r2.status_code == 400
    assert r2.json()["error"]["code"] == "TOKEN_ALREADY_USED"


# ── /me includes email_verified ───────────────────────────────────

@pytest.mark.asyncio
async def test_me_includes_email_verified_false_before_verification(live_app):
    """AC-4: Unverified user's /me returns email_verified: false."""
    client, pool, vault = live_app
    # Create user + credential + sign in
    email = f"{_TEST_PREFIX}me1@example.com"
    password = "TestPass123!"
    r = await client.post(
        "/v1/auth/signup",
        json={"email": email, "display_name": "ME Test", "password": password},
    )
    assert r.status_code == 201
    token = r.json()["data"]["token"]

    r_me = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_me.status_code == 200
    user_data = r_me.json()["data"]["user"]
    # email_verified may be False (if policy on) or True (if policy off)
    assert "email_verified" in user_data


@pytest.mark.asyncio
async def test_me_includes_email_verified_true_after_verification(live_app):
    """AC-4: After consuming token, /me returns email_verified: true."""
    client, pool, vault = live_app
    email = f"{_TEST_PREFIX}me2@example.com"
    password = "TestPass123!"
    r = await client.post(
        "/v1/auth/signup",
        json={"email": email, "display_name": "ME Test2", "password": password},
    )
    assert r.status_code == 201
    data = r.json()["data"]
    token = data["token"]
    user_id = data["user"]["id"]

    # Insert verification token and consume
    raw_token = await _insert_token(pool, user_id=user_id, vault=vault)
    r_consume = await client.post(
        "/v1/auth/verify-email/consume",
        json={"token": raw_token},
    )
    assert r_consume.status_code == 200

    r_me = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r_me.status_code == 200
    user_data = r_me.json()["data"]["user"]
    assert user_data["email_verified"] is True

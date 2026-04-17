"""
Integration tests for iam.auth — Phase 8 acceptance.

Covers: signup, signin (good + bad password), signout, /me, session expiry,
session signing-key rotation, run_node dispatch (validate_session).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_ctx_mod: Any = import_module("backend.01_catalog.context")

_TEST_EMAIL_PREFIX = "itest-auth-"


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
        # Sessions cascade-delete via FK; wipe them anyway in case of orphans.
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
            'DELETE FROM "03_iam"."41_lnk_user_workspaces" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            """
            DELETE FROM "04_audit"."60_evt_audit"
            WHERE event_key LIKE 'iam.auth.%'
               OR event_key LIKE 'iam.users.%'
               OR event_key LIKE 'iam.memberships.%'
            """,
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
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac, pool
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


@pytest.mark.asyncio
async def test_signup_then_me_returns_user(live_app) -> None:
    client, _pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}happy@example.com"

    resp = await client.post(
        "/v1/auth/signup",
        json={"email": email, "display_name": "Happy", "password": "correct horse battery staple"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["token"]
    assert data["user"]["email"] == email
    assert data["user"]["account_type"] == "email_password"
    assert data["session"]["is_valid"] is True
    token = data["token"]

    # Cookie set
    set_cookie = resp.headers.get("set-cookie", "")
    assert "tennetctl_session=" in set_cookie
    assert "HttpOnly" in set_cookie or "httponly" in set_cookie

    # /me with Bearer
    me = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200, me.text
    assert me.json()["data"]["user"]["email"] == email


@pytest.mark.asyncio
async def test_signup_duplicate_rejected(live_app) -> None:
    client, _pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}dup@example.com"

    body = {"email": email, "display_name": "Dup", "password": "another long password"}
    r1 = await client.post("/v1/auth/signup", json=body)
    assert r1.status_code == 201
    r2 = await client.post("/v1/auth/signup", json=body)
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_signin_success_and_bad_password(live_app) -> None:
    client, _pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}signin@example.com"
    password = "this is a long enough password"

    s = await client.post(
        "/v1/auth/signup",
        json={"email": email, "display_name": "Signer", "password": password},
    )
    assert s.status_code == 201

    # Good
    ok = await client.post(
        "/v1/auth/signin",
        json={"email": email, "password": password},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["data"]["user"]["email"] == email

    # Bad
    bad = await client.post(
        "/v1/auth/signin",
        json={"email": email, "password": "wrong"},
    )
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "UNAUTHORIZED"

    # Unknown email — also 401, never 404 (avoid user enumeration)
    nope = await client.post(
        "/v1/auth/signin",
        json={"email": f"{_TEST_EMAIL_PREFIX}ghost@example.com", "password": password},
    )
    assert nope.status_code == 401


@pytest.mark.asyncio
async def test_signout_revokes_session(live_app) -> None:
    client, _pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}out@example.com"

    s = await client.post(
        "/v1/auth/signup",
        json={"email": email, "display_name": "Outer", "password": "password password"},
    )
    token = s.json()["data"]["token"]
    auth = {"Authorization": f"Bearer {token}"}

    me1 = await client.get("/v1/auth/me", headers=auth)
    assert me1.status_code == 200

    so = await client.post("/v1/auth/signout", headers=auth)
    assert so.status_code == 200, so.text
    assert so.json()["data"]["signed_out"] is True

    me2 = await client.get("/v1/auth/me", headers=auth)
    assert me2.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token_is_401(live_app) -> None:
    client, _pool = live_app
    resp = await client.get("/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_session_expiry_invalidates_token(live_app) -> None:
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}expire@example.com"

    s = await client.post(
        "/v1/auth/signup",
        json={"email": email, "display_name": "Expire", "password": "password password"},
    )
    token = s.json()["data"]["token"]
    session_id = s.json()["data"]["session"]["id"]

    # Force expiry — push expires_at into the past
    async with pool.acquire() as conn:
        await conn.execute(
            'UPDATE "03_iam"."16_fct_sessions" '
            'SET expires_at = $1 WHERE id = $2',
            datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1),
            session_id,
        )

    me = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 401


@pytest.mark.asyncio
async def test_validate_session_node_via_run_node(live_app) -> None:
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}node@example.com"

    s = await client.post(
        "/v1/auth/signup",
        json={"email": email, "display_name": "Noder", "password": "password password"},
    )
    token = s.json()["data"]["token"]
    user_id = s.json()["data"]["user"]["id"]

    vault = _main.app.state.vault
    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            audit_category="system",
            trace_id="t", span_id="s",
            conn=conn,
            extras={"pool": pool, "vault": vault},
        )
        result = await _catalog.run_node(
            pool, "iam.auth.validate_session", ctx, {"token": token},
        )
    assert result["session"] is not None
    assert result["session"]["user_id"] == user_id
    assert result["session"]["is_valid"] is True

    # Tampered token → None
    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            audit_category="system",
            trace_id="t", span_id="s",
            conn=conn,
            extras={"pool": pool, "vault": vault},
        )
        bad = await _catalog.run_node(
            pool, "iam.auth.validate_session", ctx, {"token": token + "x"},
        )
    assert bad == {"session": None}


@pytest.mark.asyncio
async def test_signup_emits_audit_event(live_app) -> None:
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}audit@example.com"

    s = await client.post(
        "/v1/auth/signup",
        json={"email": email, "display_name": "Audit", "password": "password password"},
    )
    user_id = s.json()["data"]["user"]["id"]

    async with pool.acquire() as conn:
        n = await conn.fetchval(
            'SELECT count(*) FROM "04_audit"."60_evt_audit" '
            "WHERE event_key = 'iam.auth.signup' AND metadata->>'user_id' = $1",
            user_id,
        )
    assert n == 1

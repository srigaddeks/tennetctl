"""
Integration tests for iam.passkeys — Plan 12-03.

Covers: register_begin (gets valid options JSON), auth_begin (gets valid options),
invalid challenge errors, list/delete credential management.
Note: register_complete/auth_complete require real browser/authenticator responses
and are validated via E2E browser tests only.
"""

from __future__ import annotations

import json
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_users_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_pk_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.13_passkeys.repository"
)
_core_id: Any = import_module("backend.01_core.id")
_ctx_mod: Any = import_module("backend.01_catalog.context")

_TEST_PREFIX = "itest-pk-"


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
            'DELETE FROM "03_iam"."25_fct_iam_passkey_challenges" WHERE user_id = ANY($1::text[])',
            user_ids,
        ) if user_ids else None
        await conn.execute(
            'DELETE FROM "03_iam"."26_fct_iam_passkey_credentials" WHERE user_id = ANY($1::text[])',
            user_ids,
        ) if user_ids else None
        if not user_ids:
            return
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


async def _make_user(pool: Any, suffix: str = "u1") -> dict:
    async with pool.acquire() as conn:
        ctx = _sys_ctx(pool, conn)
        return await _users_service.create_user(
            pool, conn, ctx,
            email=f"{_TEST_PREFIX}{suffix}@example.com",
            display_name="Passkey Test User",
            account_type="email_password",
        )


async def _insert_fake_credential(pool: Any, user_id: str) -> dict:
    """Insert a fake passkey credential directly for list/delete tests."""
    async with pool.acquire() as conn:
        return await _pk_repo.create_credential(
            conn,
            cred_id=_core_id.uuid7(),
            user_id=user_id,
            credential_id_b64="ZmFrZS1jcmVkZW50aWFsLWlk",
            public_key_b64="ZmFrZS1wdWJsaWMta2V5",
            aaguid="",
            sign_count=0,
            device_name="Test Device",
        )


# ─── Register tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_begin_requires_auth(live_app):
    """Register begin requires a session."""
    client, _pool = live_app
    r = await client.post("/v1/auth/passkeys/register/begin", json={"device_name": "Test"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_register_begin_returns_options(live_app):
    """Authenticated register begin returns valid WebAuthn options JSON."""
    client, pool = live_app
    user = await _make_user(pool, "reg1")

    # Mint a session for the user to authenticate
    vault = _main.app.state.vault
    from importlib import import_module as _im
    _sess = _im("backend.02_features.03_iam.sub_features.09_sessions.service")
    async with pool.acquire() as conn:
        token, _session = await _sess.mint_session(conn, vault_client=vault, user_id=user["id"], org_id=None)

    r = await client.post(
        "/v1/auth/passkeys/register/begin",
        json={"device_name": "My Passkey"},
        cookies={"tennetctl_session": token},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    opts = json.loads(data["data"]["options_json"])
    assert "challenge" in opts
    assert opts["rp"]["id"] == "localhost"
    assert "challenge_id" in data["data"]


# ─── Auth begin tests ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_begin_no_passkeys_returns_404(live_app):
    """Auth begin for user with no passkeys returns 404."""
    client, pool = live_app
    user = await _make_user(pool, "auth1")
    r = await client.post("/v1/auth/passkeys/auth/begin", json={"email": user["email"]})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NO_PASSKEYS"


@pytest.mark.asyncio
async def test_auth_begin_unknown_user_returns_404(live_app):
    client, _pool = live_app
    r = await client.post("/v1/auth/passkeys/auth/begin", json={"email": "nobody-xyz@example.com"})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_auth_begin_with_passkey_returns_options(live_app):
    """Auth begin for user with a passkey returns valid options."""
    client, pool = live_app
    user = await _make_user(pool, "auth2")
    await _insert_fake_credential(pool, user["id"])
    r = await client.post("/v1/auth/passkeys/auth/begin", json={"email": user["email"]})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    opts = json.loads(data["data"]["options_json"])
    assert "challenge" in opts
    assert len(opts.get("allowCredentials", [])) > 0


# ─── Complete tests (error cases only) ───────────────────────────────────────

@pytest.mark.asyncio
async def test_register_complete_invalid_challenge(live_app):
    """register_complete with bogus challenge_id → 401."""
    client, pool = live_app
    user = await _make_user(pool, "cmp1")
    vault = _main.app.state.vault
    from importlib import import_module as _im
    _sess = _im("backend.02_features.03_iam.sub_features.09_sessions.service")
    async with pool.acquire() as conn:
        token, _ = await _sess.mint_session(conn, vault_client=vault, user_id=user["id"], org_id=None)

    r = await client.post(
        "/v1/auth/passkeys/register/complete",
        json={"challenge_id": "nonexistent-id", "credential_json": "{}"},
        cookies={"tennetctl_session": token},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CHALLENGE"


@pytest.mark.asyncio
async def test_auth_complete_invalid_challenge(live_app):
    """auth_complete with bogus challenge_id → 401."""
    client, _pool = live_app
    r = await client.post(
        "/v1/auth/passkeys/auth/complete",
        json={"challenge_id": "nonexistent-id", "credential_json": "{}"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CHALLENGE"


# ─── List/delete tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_passkeys_returns_credentials(live_app):
    """List passkeys returns enrolled credentials for the user."""
    client, pool = live_app
    user = await _make_user(pool, "lst1")
    await _insert_fake_credential(pool, user["id"])

    vault = _main.app.state.vault
    from importlib import import_module as _im
    _sess = _im("backend.02_features.03_iam.sub_features.09_sessions.service")
    async with pool.acquire() as conn:
        token, _ = await _sess.mint_session(conn, vault_client=vault, user_id=user["id"], org_id=None)

    r = await client.get("/v1/auth/passkeys", cookies={"tennetctl_session": token})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["data"]["total"] == 1
    assert data["data"]["items"][0]["device_name"] == "Test Device"


@pytest.mark.asyncio
async def test_delete_passkey(live_app):
    """Delete a passkey removes it from list."""
    client, pool = live_app
    user = await _make_user(pool, "del1")
    cred = await _insert_fake_credential(pool, user["id"])

    vault = _main.app.state.vault
    from importlib import import_module as _im
    _sess = _im("backend.02_features.03_iam.sub_features.09_sessions.service")
    async with pool.acquire() as conn:
        token, _ = await _sess.mint_session(conn, vault_client=vault, user_id=user["id"], org_id=None)

    r = await client.delete(f"/v1/auth/passkeys/{cred['id']}", cookies={"tennetctl_session": token})
    assert r.status_code == 204

    r2 = await client.get("/v1/auth/passkeys", cookies={"tennetctl_session": token})
    assert r2.json()["data"]["total"] == 0

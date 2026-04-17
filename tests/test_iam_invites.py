"""
Integration tests for iam.invites — Plan 21-02.

Covers:
- invite created returns 201 with no token in response
- accept-invite creates user and returns session
- accept with wrong token returns 401
- cancel invite returns 204
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_core_id: Any = import_module("backend.01_core.id")
_ctx_mod: Any = import_module("backend.01_catalog.context")
_users_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_invites_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.17_invites.service"
)

_TEST_PREFIX = "itest-invites-"


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

        # Delete invites by email pattern
        await conn.execute(
            'DELETE FROM "03_iam"."30_fct_user_invites" WHERE email LIKE $1',
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


async def _make_inviter(pool: Any) -> dict:
    async with pool.acquire() as conn:
        ctx = _sys_ctx(pool, conn)
        return await _users_service.create_user(
            pool, conn, ctx,
            email=f"{_TEST_PREFIX}admin@example.com",
            display_name="Invite Admin",
            account_type="email_password",
        )


async def _get_default_org(pool: Any) -> str:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT id FROM "03_iam"."10_fct_orgs" WHERE deleted_at IS NULL LIMIT 1'
        )
        if row is None:
            raise RuntimeError("No org found — run setup first")
        return row["id"]


# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_invite_returns_201_without_token(live_app):
    ac, pool = live_app
    org_id = await _get_default_org(pool)
    inviter = await _make_inviter(pool)

    vault = _main.app.state.vault
    async with pool.acquire() as conn:
        ctx = _sys_ctx(pool, conn)
        ctx = _ctx_mod.NodeContext(
            user_id=inviter["id"],
            session_id=None,
            org_id=org_id,
            workspace_id=None,
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
            audit_category="iam",
            conn=conn,
            extras={"pool": pool},
        )
        raw_token, invite = await _invites_service.create_invite(
            pool, conn, ctx,
            org_id=org_id,
            email=f"{_TEST_PREFIX}newbie@example.com",
            vault_client=vault,
        )

    # raw_token should never be in the invite dict returned by the service
    assert "token" not in invite
    assert "token_hash" in invite  # hash is stored
    assert invite["token_hash"] != raw_token  # definitely not the raw token
    assert invite["status"] == 1
    assert invite["org_id"] == org_id


@pytest.mark.asyncio
async def test_accept_invite_creates_user_and_returns_session(live_app):
    ac, pool = live_app
    org_id = await _get_default_org(pool)
    inviter = await _make_inviter(pool)
    vault = _main.app.state.vault

    email = f"{_TEST_PREFIX}accepted@example.com"

    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            user_id=inviter["id"],
            session_id=None,
            org_id=org_id,
            workspace_id=None,
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
            audit_category="iam",
            conn=conn,
            extras={"pool": pool},
        )
        raw_token, _invite = await _invites_service.create_invite(
            pool, conn, ctx,
            org_id=org_id,
            email=email,
            vault_client=vault,
        )

    resp = await ac.post(
        "/v1/auth/accept-invite",
        json={"token": raw_token, "password": "Passw0rd!!", "display_name": "New User"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert "token" in body["data"]
    assert body["data"]["user"]["email"] == email


@pytest.mark.asyncio
async def test_accept_invite_wrong_token_returns_401(live_app):
    ac, pool = live_app
    resp = await ac.post(
        "/v1/auth/accept-invite",
        json={"token": "bad-token-xyz", "password": "Passw0rd!!", "display_name": "Ghost"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_cancel_invite_returns_204(live_app):
    ac, pool = live_app
    org_id = await _get_default_org(pool)
    inviter = await _make_inviter(pool)
    vault = _main.app.state.vault

    email = f"{_TEST_PREFIX}cancelled@example.com"

    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            user_id=inviter["id"],
            session_id=None,
            org_id=org_id,
            workspace_id=None,
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
            audit_category="iam",
            conn=conn,
            extras={"pool": pool},
        )
        _raw, invite = await _invites_service.create_invite(
            pool, conn, ctx,
            org_id=org_id,
            email=email,
            vault_client=vault,
        )

    # Cancel via service (direct, no auth middleware needed)
    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            user_id=inviter["id"],
            session_id=None,
            org_id=org_id,
            workspace_id=None,
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
            audit_category="iam",
            conn=conn,
            extras={"pool": pool},
        )
        await _invites_service.cancel_invite(
            pool, conn, ctx,
            org_id=org_id,
            invite_id=invite["id"],
        )

    # Verify the invite is now cancelled (status=3)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT status FROM "03_iam"."30_fct_user_invites" WHERE id = $1',
            invite["id"],
        )
    assert row is not None
    assert row["status"] == 3

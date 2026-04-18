"""
MFA enforcement policy integration tests.

Tests cover: get policy (default off), enable policy, MFA gate blocks sign-in,
MFA gate passes when enrolled, disable policy lifts restriction.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")

_TEST_EMAIL_PREFIX = "itest-mfa-"
_TEST_ORG_SLUG = "mfa-test-org"
_MFA_PATH = "/v1/iam/mfa-policy"
_SIGNIN_PATH = "/v1/auth/signin"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        user_rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3 AND d.code = 'email'
              AND a.key_text LIKE $1
            """,
            f"{_TEST_EMAIL_PREFIX}%",
        )
        user_ids = [r["user_id"] for r in user_rows]
        if user_ids:
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
                'DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "04_audit"."60_evt_audit" WHERE metadata->>\'user_id\' = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
                user_ids,
            )
        await conn.execute(
            """DELETE FROM "02_vault"."10_fct_vault_entries" WHERE key = 'iam.policy.mfa.required'
               AND org_id IN (SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = $1)""",
            _TEST_ORG_SLUG,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."10_fct_orgs" WHERE slug = $1', _TEST_ORG_SLUG
        )


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        vault = _main.app.state.vault

        await _cleanup(pool)

        _orgs_svc: Any = import_module("backend.02_features.03_iam.sub_features.01_orgs.service")
        _users_svc: Any = import_module("backend.02_features.03_iam.sub_features.03_users.service")
        _creds_svc: Any = import_module("backend.02_features.03_iam.sub_features.08_credentials.service")
        _sessions_svc: Any = import_module("backend.02_features.03_iam.sub_features.09_sessions.service")
        _catalog_ctx: Any = import_module("backend.01_catalog.context")
        _core_id: Any = import_module("backend.01_core.id")

        ctx = _catalog_ctx.NodeContext(
            user_id=None, session_id=None, org_id=None, workspace_id=None,
            trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
        )

        async with pool.acquire() as conn:
            org = await _orgs_svc.create_org(pool, conn, ctx, slug=_TEST_ORG_SLUG, display_name="MFA Test Org")
        org_id = org["id"]

        async with pool.acquire() as conn:
            user = await _users_svc.create_user(
                pool, conn, ctx, account_type="email_password",
                email=f"{_TEST_EMAIL_PREFIX}user@example.com", display_name="MFA User",
            )
            await _creds_svc.set_password(conn, vault_client=vault, user_id=user["id"], value="TestPass123!")
            token, _ = await _sessions_svc.mint_session(conn, vault_client=vault, user_id=user["id"], org_id=org_id)

        try:
            yield {
                "app": _main.app, "pool": pool, "vault": vault,
                "org_id": org_id, "token": token, "user_id": user["id"],
                "email": f"{_TEST_EMAIL_PREFIX}user@example.com",
            }
        finally:
            await _cleanup(pool)


@pytest.fixture
async def authed_client(live_app):
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
    ) as client:
        client.cookies.set("tennetctl_session", live_app["token"])
        client.headers.update({"x-org-id": live_app["org_id"]})
        yield client


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_mfa_policy_default_off(authed_client):
    resp = await authed_client.get(_MFA_PATH)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["required"] is False
    assert data["totp_enrolled"] is False


@pytest.mark.asyncio
async def test_enable_mfa_policy(authed_client):
    resp = await authed_client.put(_MFA_PATH, json={"required": True})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["required"] is True

    # GET confirms it's enabled
    get_resp = await authed_client.get(_MFA_PATH)
    assert get_resp.json()["data"]["required"] is True


@pytest.mark.asyncio
async def test_disable_mfa_policy(authed_client):
    await authed_client.put(_MFA_PATH, json={"required": True})
    resp = await authed_client.put(_MFA_PATH, json={"required": False})
    assert resp.status_code == 200
    assert resp.json()["data"]["required"] is False


@pytest.mark.asyncio
async def test_mfa_gate_blocks_signin_when_required(live_app, authed_client):
    """When MFA is required and user has no TOTP, sign-in is blocked."""
    # Enable MFA for the org
    await authed_client.put(_MFA_PATH, json={"required": True})

    # Sign-in should fail with MFA_ENROLLMENT_REQUIRED
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
    ) as client:
        resp = await client.post(
            _SIGNIN_PATH,
            json={"email": live_app["email"], "password": "TestPass123!"},
            headers={"x-org-id": live_app["org_id"]},
        )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "MFA_ENROLLMENT_REQUIRED"


@pytest.mark.asyncio
async def test_mfa_gate_passes_when_enrolled(live_app, authed_client):
    """When MFA is required and user is enrolled, sign-in succeeds."""
    await authed_client.put(_MFA_PATH, json={"required": True})

    # Mock TOTP enrollment for the user
    _mfa_svc: Any = import_module("backend.02_features.03_iam.sub_features.24_mfa_policy.service")
    with patch.object(
        _mfa_svc._otp_repo, "list_totp_credentials",
        new=AsyncMock(return_value=[{"id": "mock-cred"}]),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=live_app["app"]),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                _SIGNIN_PATH,
                json={"email": live_app["email"], "password": "TestPass123!"},
                headers={"x-org-id": live_app["org_id"]},
            )
    assert resp.status_code == 200

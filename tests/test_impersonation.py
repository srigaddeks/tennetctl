"""
Admin impersonation integration tests.

Tests cover: start impersonation, end impersonation, status check,
non-admin rejection, self-impersonation rejection, nested impersonation rejection.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")

_TEST_EMAIL_PREFIX = "itest-imp-"
_TEST_ORG_SLUG = "imp-test-org"
_IMP_PATH = "/v1/iam/impersonation"


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
                'DELETE FROM "03_iam"."45_lnk_impersonations" WHERE impersonator_user_id = ANY($1::text[]) OR impersonated_user_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."42_lnk_user_roles" WHERE user_id = ANY($1::text[])',
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
                'DELETE FROM "04_audit"."60_evt_audit" WHERE metadata->>\'user_id\' = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
                user_ids,
            )
        await conn.execute(
            """DELETE FROM "03_iam"."13_fct_roles" WHERE org_id IN (
                SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = $1)""",
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
        _roles_svc: Any = import_module("backend.02_features.03_iam.sub_features.04_roles.service")
        _sessions_svc: Any = import_module("backend.02_features.03_iam.sub_features.09_sessions.service")
        _catalog_ctx: Any = import_module("backend.01_catalog.context")
        _core_id: Any = import_module("backend.01_core.id")

        ctx = _catalog_ctx.NodeContext(
            user_id=None, session_id=None, org_id=None, workspace_id=None,
            trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
        )

        async with pool.acquire() as conn:
            org = await _orgs_svc.create_org(pool, conn, ctx, slug=_TEST_ORG_SLUG, display_name="Imp Test Org")
        org_id = org["id"]

        # Get or create system role (super-admin marker)
        _roles_repo: Any = import_module("backend.02_features.03_iam.sub_features.04_roles.repository")
        async with pool.acquire() as conn:
            existing_role = await _roles_repo.get_by_org_code(conn, None, "superadmin")
            if existing_role:
                system_role = existing_role
            else:
                system_role = await _roles_svc.create_role(
                    pool, conn, ctx, org_id=None, role_type="system",
                    code="superadmin", label="Super Admin",
                )

        # Create admin user and assign system role
        async with pool.acquire() as conn:
            admin = await _users_svc.create_user(
                pool, conn, ctx, account_type="email_password",
                email=f"{_TEST_EMAIL_PREFIX}admin@example.com", display_name="Imp Admin",
            )
            await conn.execute(
                'INSERT INTO "03_iam"."42_lnk_user_roles" (id, user_id, role_id, org_id, created_by) '
                'VALUES ($1, $2, $3, $4, $5)',
                _core_id.uuid7(), admin["id"], system_role["id"], org_id, "sys",
            )
            admin_token, _ = await _sessions_svc.mint_session(conn, vault_client=vault, user_id=admin["id"], org_id=org_id)

        # Create regular target user
        async with pool.acquire() as conn:
            target = await _users_svc.create_user(
                pool, conn, ctx, account_type="email_password",
                email=f"{_TEST_EMAIL_PREFIX}target@example.com", display_name="Target User",
            )
            non_admin_token, _ = await _sessions_svc.mint_session(conn, vault_client=vault, user_id=target["id"], org_id=org_id)

        try:
            yield {
                "app": _main.app, "pool": pool, "vault": vault,
                "org_id": org_id, "admin_token": admin_token, "admin_id": admin["id"],
                "target_id": target["id"], "target_token": non_admin_token,
                "system_role_id": system_role["id"],
            }
        finally:
            await _cleanup(pool)


@pytest.fixture
async def admin_client(live_app):
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
    ) as client:
        client.cookies.set("tennetctl_session", live_app["admin_token"])
        client.headers.update({"x-org-id": live_app["org_id"]})
        yield client


@pytest.fixture
async def target_client(live_app):
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
    ) as client:
        client.cookies.set("tennetctl_session", live_app["target_token"])
        client.headers.update({"x-org-id": live_app["org_id"]})
        yield client


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_impersonation(live_app, admin_client):
    resp = await admin_client.post(_IMP_PATH, json={"target_user_id": live_app["target_id"]})
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert "session_token" in data
    assert data["impersonated_user_id"] == live_app["target_id"]
    assert "expires_at" in data


@pytest.mark.asyncio
async def test_impersonated_session_acts_as_target(live_app):
    # Start impersonation and use the returned token to call /v1/auth/me
    admin_client = AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        cookies={"tennetctl_session": live_app["admin_token"]},
        headers={"x-org-id": live_app["org_id"]},
    )
    async with admin_client as client:
        imp_resp = await client.post(_IMP_PATH, json={"target_user_id": live_app["target_id"]})
    imp_token = imp_resp.json()["data"]["session_token"]

    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        cookies={"tennetctl_session": imp_token},
    ) as imp_client:
        me_resp = await imp_client.get("/v1/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["user"]["id"] == live_app["target_id"]


@pytest.mark.asyncio
async def test_get_status_no_impersonation(admin_client):
    resp = await admin_client.get(_IMP_PATH)
    assert resp.status_code == 200
    assert resp.json()["data"]["active"] is False


@pytest.mark.asyncio
async def test_end_impersonation(live_app):
    # Start impersonation with the returned token, then call DELETE to end it
    admin_client = AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        cookies={"tennetctl_session": live_app["admin_token"]},
        headers={"x-org-id": live_app["org_id"]},
    )
    async with admin_client as client:
        imp_resp = await client.post(_IMP_PATH, json={"target_user_id": live_app["target_id"]})
    imp_token = imp_resp.json()["data"]["session_token"]

    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        cookies={"tennetctl_session": imp_token},
    ) as imp_client:
        del_resp = await imp_client.delete(_IMP_PATH)
        assert del_resp.status_code == 204
        # Session should now be invalid
        me_resp = await imp_client.get("/v1/auth/me")
    assert me_resp.status_code == 401


@pytest.mark.asyncio
async def test_non_admin_cannot_impersonate(live_app, target_client):
    resp = await target_client.post(_IMP_PATH, json={"target_user_id": live_app["admin_id"]})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cannot_impersonate_self(live_app, admin_client):
    resp = await admin_client.post(_IMP_PATH, json={"target_user_id": live_app["admin_id"]})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cannot_impersonate_admin(live_app, admin_client):
    """Cannot impersonate another super-admin."""
    _core_id: Any = import_module("backend.01_core.id")
    _users_svc: Any = import_module("backend.02_features.03_iam.sub_features.03_users.service")
    _catalog_ctx: Any = import_module("backend.01_catalog.context")
    pool = live_app["pool"]
    ctx = _catalog_ctx.NodeContext(
        user_id=None, session_id=None, org_id=None, workspace_id=None,
        trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
    )
    async with pool.acquire() as conn:
        admin2 = await _users_svc.create_user(
            pool, conn, ctx, account_type="email_password",
            email=f"{_TEST_EMAIL_PREFIX}admin2@example.com", display_name="Admin2",
        )
        await conn.execute(
            'INSERT INTO "03_iam"."42_lnk_user_roles" (id, user_id, role_id, org_id, created_by) '
            'VALUES ($1, $2, $3, $4, $5)',
            _core_id.uuid7(), admin2["id"], live_app["system_role_id"], live_app["org_id"], "sys",
        )
    resp = await admin_client.post(_IMP_PATH, json={"target_user_id": admin2["id"]})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_nested_impersonation_rejected(live_app):
    """Impersonation session cannot start another impersonation."""
    admin_client = AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        cookies={"tennetctl_session": live_app["admin_token"]},
        headers={"x-org-id": live_app["org_id"]},
    )
    async with admin_client as client:
        imp_resp = await client.post(_IMP_PATH, json={"target_user_id": live_app["target_id"]})
    imp_token = imp_resp.json()["data"]["session_token"]

    _core_id: Any = import_module("backend.01_core.id")
    _users_svc: Any = import_module("backend.02_features.03_iam.sub_features.03_users.service")
    _catalog_ctx: Any = import_module("backend.01_catalog.context")
    pool = live_app["pool"]
    ctx = _catalog_ctx.NodeContext(
        user_id=None, session_id=None, org_id=None, workspace_id=None,
        trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
    )
    async with pool.acquire() as conn:
        other = await _users_svc.create_user(
            pool, conn, ctx, account_type="email_password",
            email=f"{_TEST_EMAIL_PREFIX}other@example.com", display_name="Other",
        )

    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        cookies={"tennetctl_session": imp_token},
        headers={"x-org-id": live_app["org_id"]},
    ) as imp_client:
        resp = await imp_client.post(_IMP_PATH, json={"target_user_id": other["id"]})
    assert resp.status_code in (403, 409)

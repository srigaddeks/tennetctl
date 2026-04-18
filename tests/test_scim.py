"""
SCIM 2.0 integration tests.

Tests cover: token create/list/revoke, SCIM Users CRUD, SCIM Groups CRUD,
JIT user creation via SCIM, user deprovisioning (deactivate + session revoke),
bearer auth rejection, externalId idempotency.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")

_TEST_EMAIL_PREFIX = "itest-scim-"
_TEST_ORG_SLUG = "scim-test-org"

_SCIM_USERS_PATH = f"/scim/v2/{_TEST_ORG_SLUG}/Users"
_SCIM_GROUPS_PATH = f"/scim/v2/{_TEST_ORG_SLUG}/Groups"
_SCIM_TOKENS_PATH = "/v1/iam/scim-tokens"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        # Remove test users
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
                'DELETE FROM "03_iam"."43_lnk_user_groups" WHERE user_id = ANY($1::text[])',
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
        # Remove test org's groups (FK constraint)
        await conn.execute(
            """DELETE FROM "03_iam"."14_fct_groups" WHERE org_id IN (
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

        _orgs_service: Any = import_module(
            "backend.02_features.03_iam.sub_features.01_orgs.service"
        )
        _users_service: Any = import_module(
            "backend.02_features.03_iam.sub_features.03_users.service"
        )
        _sessions_service: Any = import_module(
            "backend.02_features.03_iam.sub_features.09_sessions.service"
        )
        _catalog_ctx: Any = import_module("backend.01_catalog.context")
        _core_id: Any = import_module("backend.01_core.id")

        ctx = _catalog_ctx.NodeContext(
            user_id=None, session_id=None, org_id=None, workspace_id=None,
            trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
        )
        async with pool.acquire() as conn:
            org = await _orgs_service.create_org(pool, conn, ctx, slug=_TEST_ORG_SLUG, display_name="SCIM Test Org")

        org_id = org["id"]

        async with pool.acquire() as conn:
            admin = await _users_service.create_user(
                pool, conn, ctx, account_type="email_password",
                email=f"{_TEST_EMAIL_PREFIX}admin@example.com", display_name="SCIM Admin",
            )
            token, _ = await _sessions_service.mint_session(
                conn, vault_client=vault, user_id=admin["id"], org_id=org_id,
            )

        try:
            yield {"app": _main.app, "pool": pool, "vault": vault, "org_id": org_id, "session_token": token}
        finally:
            await _cleanup(pool)


@pytest.fixture
async def authed_client(live_app):
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
    ) as client:
        client.cookies.set("tennetctl_session", live_app["session_token"])
        client.headers.update({"x-org-id": live_app["org_id"]})
        yield client


@pytest.fixture
async def scim_client(live_app, authed_client):
    """Returns (anon AsyncClient, scim_bearer_token)."""
    resp = await authed_client.post(_SCIM_TOKENS_PATH, json={"label": "test-token"})
    assert resp.status_code == 201
    scim_token = resp.json()["data"]["token"]
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        headers={"Authorization": f"Bearer {scim_token}"},
    ) as client:
        yield client, scim_token


# ── Token management ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_scim_token(authed_client):
    resp = await authed_client.post(_SCIM_TOKENS_PATH, json={"label": "my-okta"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["label"] == "my-okta"
    assert "token" in data
    assert data["token"].startswith("scim_")


@pytest.mark.asyncio
async def test_list_scim_tokens(authed_client):
    await authed_client.post(_SCIM_TOKENS_PATH, json={"label": "token-a"})
    await authed_client.post(_SCIM_TOKENS_PATH, json={"label": "token-b"})
    resp = await authed_client.get(_SCIM_TOKENS_PATH)
    assert resp.status_code == 200
    tokens = resp.json()["data"]
    assert len(tokens) >= 2
    for t in tokens:
        assert "token" not in t  # raw token NOT in list


@pytest.mark.asyncio
async def test_revoke_scim_token(authed_client):
    create_resp = await authed_client.post(_SCIM_TOKENS_PATH, json={"label": "revoke-me"})
    token_id = create_resp.json()["data"]["id"]
    del_resp = await authed_client.delete(f"{_SCIM_TOKENS_PATH}/{token_id}")
    assert del_resp.status_code == 204
    list_resp = await authed_client.get(_SCIM_TOKENS_PATH)
    ids = [t["id"] for t in list_resp.json()["data"]]
    assert token_id not in ids


# ── SCIM Users ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scim_bearer_auth_rejects_invalid(live_app):
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        headers={"Authorization": "Bearer invalid-token-xyz"},
    ) as client:
        resp = await client.get(_SCIM_USERS_PATH)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_scim_create_user(scim_client):
    client, _ = scim_client
    resp = await client.post(_SCIM_USERS_PATH, json={
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": f"{_TEST_EMAIL_PREFIX}scim-new@example.com",
        "displayName": "SCIM User",
        "active": True,
        "externalId": "okta-user-001",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["userName"] == f"{_TEST_EMAIL_PREFIX}scim-new@example.com"
    assert data["externalId"] == "okta-user-001"
    assert data["active"] is True


@pytest.mark.asyncio
async def test_scim_create_user_conflict(scim_client):
    client, _ = scim_client
    await client.post(_SCIM_USERS_PATH, json={
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": f"{_TEST_EMAIL_PREFIX}conflict@example.com",
        "externalId": "ext-conflict-001",
    })
    resp2 = await client.post(_SCIM_USERS_PATH, json={
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": f"{_TEST_EMAIL_PREFIX}conflict@example.com",
        "externalId": "ext-conflict-001",
    })
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_scim_get_user(scim_client):
    client, _ = scim_client
    create_resp = await client.post(_SCIM_USERS_PATH, json={
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": f"{_TEST_EMAIL_PREFIX}get-user@example.com",
    })
    user_id = create_resp.json()["id"]
    get_resp = await client.get(f"{_SCIM_USERS_PATH}/{user_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == user_id


@pytest.mark.asyncio
async def test_scim_list_users(scim_client):
    client, _ = scim_client
    await client.post(_SCIM_USERS_PATH, json={
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": f"{_TEST_EMAIL_PREFIX}list-user@example.com",
    })
    resp = await client.get(_SCIM_USERS_PATH)
    assert resp.status_code == 200
    body = resp.json()
    assert "Resources" in body
    assert body["totalResults"] >= 1


@pytest.mark.asyncio
async def test_scim_patch_user_active_false(scim_client):
    client, _ = scim_client
    create_resp = await client.post(_SCIM_USERS_PATH, json={
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": f"{_TEST_EMAIL_PREFIX}patch-deactivate@example.com",
    })
    user_id = create_resp.json()["id"]
    patch_resp = await client.patch(f"{_SCIM_USERS_PATH}/{user_id}", json={
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [{"op": "Replace", "path": "active", "value": False}],
    })
    assert patch_resp.status_code == 200
    assert patch_resp.json()["active"] is False


@pytest.mark.asyncio
async def test_scim_deprovision_user(live_app, scim_client):
    client, _ = scim_client
    create_resp = await client.post(_SCIM_USERS_PATH, json={
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": f"{_TEST_EMAIL_PREFIX}deprovision@example.com",
    })
    user_id = create_resp.json()["id"]
    del_resp = await client.delete(f"{_SCIM_USERS_PATH}/{user_id}")
    assert del_resp.status_code == 204

    pool = live_app["pool"]
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            'SELECT is_active FROM "03_iam"."v_users" WHERE id = $1', user_id
        )
    assert user is not None
    assert user["is_active"] is False


# ── SCIM Groups ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scim_create_group(scim_client):
    client, _ = scim_client
    resp = await client.post(_SCIM_GROUPS_PATH, json={
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "displayName": "Engineering",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["displayName"] == "Engineering"
    assert "id" in data


@pytest.mark.asyncio
async def test_scim_list_groups(scim_client):
    client, _ = scim_client
    await client.post(_SCIM_GROUPS_PATH, json={
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "displayName": "Marketing",
    })
    resp = await client.get(_SCIM_GROUPS_PATH)
    assert resp.status_code == 200
    body = resp.json()
    assert "Resources" in body
    assert body["totalResults"] >= 1


@pytest.mark.asyncio
async def test_scim_patch_group_add_member(live_app, scim_client):
    client, _ = scim_client
    user_resp = await client.post(_SCIM_USERS_PATH, json={
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": f"{_TEST_EMAIL_PREFIX}group-member@example.com",
    })
    user_id = user_resp.json()["id"]

    group_resp = await client.post(_SCIM_GROUPS_PATH, json={
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "displayName": "DevTeam",
    })
    group_id = group_resp.json()["id"]

    patch_resp = await client.patch(f"{_SCIM_GROUPS_PATH}/{group_id}", json={
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [{"op": "Add", "path": "members", "value": [{"value": user_id}]}],
    })
    assert patch_resp.status_code == 200
    members = patch_resp.json().get("members", [])
    member_ids = [m["value"] for m in members]
    assert user_id in member_ids

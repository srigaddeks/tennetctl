"""Integration tests for featureflags.permissions."""
from __future__ import annotations

import os
from dataclasses import replace
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_ctx_mod: Any = import_module("backend.01_catalog.context")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_FLAG_PREFIX = "itest_ffp_"
_ROLE_CODE_PREFIX = "itest_ffp_role_"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        # flags with our prefix
        flag_rows = await conn.fetch(
            'SELECT id FROM "09_featureflags"."10_fct_flags" WHERE flag_key LIKE $1',
            f"{_FLAG_PREFIX}%",
        )
        flag_ids = [r["id"] for r in flag_rows]

        # Roles with our prefix
        role_rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS id FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 4 AND d.code = 'code'
              AND a.key_text LIKE $1
            """,
            f"{_ROLE_CODE_PREFIX}%",
        )
        role_ids = [r["id"] for r in role_rows]

        # Delete grants first (FK safe)
        if flag_ids or role_ids:
            await conn.execute(
                'DELETE FROM "09_featureflags"."40_lnk_role_flag_permissions" '
                "WHERE flag_id = ANY($1::text[]) OR role_id = ANY($2::text[])",
                flag_ids or [""], role_ids or [""],
            )
            await conn.execute(
                "DELETE FROM \"04_audit\".\"60_evt_audit\" "
                "WHERE event_key LIKE 'featureflags.permissions.%' "
                "AND (metadata->>'flag_id' = ANY($1::text[]) OR metadata->>'role_id' = ANY($2::text[]))",
                flag_ids or [""], role_ids or [""],
            )

        if flag_ids:
            await conn.execute(
                "DELETE FROM \"04_audit\".\"60_evt_audit\" "
                "WHERE event_key LIKE 'featureflags.flags.%' AND metadata->>'flag_id' = ANY($1::text[])",
                flag_ids,
            )
            await conn.execute(
                'DELETE FROM "09_featureflags"."11_fct_flag_states" WHERE flag_id = ANY($1::text[])',
                flag_ids,
            )
            await conn.execute(
                'DELETE FROM "09_featureflags"."10_fct_flags" WHERE id = ANY($1::text[])',
                flag_ids,
            )
        if role_ids:
            await conn.execute(
                "DELETE FROM \"04_audit\".\"60_evt_audit\" "
                "WHERE event_key LIKE 'iam.roles.%' AND metadata->>'role_id' = ANY($1::text[])",
                role_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id=4 AND entity_id = ANY($1::text[])',
                role_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."13_fct_roles" WHERE id = ANY($1::text[])',
                role_ids,
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


async def _make_flag(client: AsyncClient, key: str) -> str:
    r = await client.post(
        "/v1/flags",
        json={"scope": "global", "flag_key": key, "value_type": "boolean", "default_value": False},
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


async def _make_role(client: AsyncClient, code: str) -> str:
    r = await client.post(
        "/v1/roles",
        json={"org_id": None, "role_type": "custom", "code": code, "label": code},
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


@pytest.mark.asyncio
async def test_grant_revoke_permission(live_app) -> None:
    client, pool = live_app
    flag_id = await _make_flag(client, f"{_FLAG_PREFIX}alpha")
    role_id = await _make_role(client, f"{_ROLE_CODE_PREFIX}editors")

    # Grant write
    r = await client.post(
        "/v1/flag-permissions",
        json={"role_id": role_id, "flag_id": flag_id, "permission": "write"},
    )
    assert r.status_code == 201, r.text
    grant = r.json()["data"]
    assert grant["permission"] == "write"
    assert grant["permission_rank"] == 3

    # Duplicate grant → 409
    r = await client.post(
        "/v1/flag-permissions",
        json={"role_id": role_id, "flag_id": flag_id, "permission": "write"},
    )
    assert r.status_code == 409

    # List filtered by flag_id returns our grant
    r = await client.get(f"/v1/flag-permissions?flag_id={flag_id}")
    assert r.status_code == 200
    assert any(g["id"] == grant["id"] for g in r.json()["data"])

    # Audit event
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT count(*) FROM \"04_audit\".\"60_evt_audit\" "
            "WHERE event_key='featureflags.permissions.granted' AND metadata->>'grant_id'=$1",
            grant["id"],
        )
    assert count == 1

    # Revoke
    r = await client.delete(f"/v1/flag-permissions/{grant['id']}")
    assert r.status_code == 204

    # Revoke-audit
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT count(*) FROM \"04_audit\".\"60_evt_audit\" "
            "WHERE event_key='featureflags.permissions.revoked' AND metadata->>'grant_id'=$1",
            grant["id"],
        )
    assert count == 1


@pytest.mark.asyncio
async def test_grant_rejects_missing_flag_or_role(live_app) -> None:
    client, _pool = live_app
    flag_id = await _make_flag(client, f"{_FLAG_PREFIX}beta")
    role_id = await _make_role(client, f"{_ROLE_CODE_PREFIX}readers")
    missing = "00000000-0000-0000-0000-000000000000"

    r = await client.post(
        "/v1/flag-permissions",
        json={"role_id": role_id, "flag_id": missing, "permission": "view"},
    )
    assert r.status_code == 404

    r = await client.post(
        "/v1/flag-permissions",
        json={"role_id": missing, "flag_id": flag_id, "permission": "view"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_max_rank_helper(live_app) -> None:
    """Direct repo call to verify permission rank resolution logic."""
    client, pool = live_app
    flag_id = await _make_flag(client, f"{_FLAG_PREFIX}gamma")
    role_id = await _make_role(client, f"{_ROLE_CODE_PREFIX}admins")

    # Grant 'admin' (rank 4) to the role
    r = await client.post(
        "/v1/flag-permissions",
        json={"role_id": role_id, "flag_id": flag_id, "permission": "admin"},
    )
    assert r.status_code == 201

    # Build a user + attach the role
    r = await client.post(
        "/v1/users",
        json={
            "account_type": "email_password",
            "email": "itest-members-ffp@example.com",
            "display_name": "FFP User",
        },
    )
    user_id = r.json()["data"]["id"]

    # Need an org to satisfy lnk_user_roles.org_id NOT NULL
    r = await client.post("/v1/orgs", json={"slug": "itest-ffp-org", "display_name": "FFP Org"})
    assert r.status_code == 201
    ffp_org_id = r.json()["data"]["id"]

    # Assign user → role via a direct insert (we don't have a user_role HTTP endpoint in v0.1 — memberships cover org/workspace only).
    import uuid
    lnk_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        await conn.execute(
            'INSERT INTO "03_iam"."42_lnk_user_roles" (id, user_id, role_id, org_id, created_by) '
            'VALUES ($1, $2, $3, $4, $5)',
            lnk_id, user_id, role_id, ffp_org_id, "sys",
        )

    # Call the repo helper directly
    _repo = import_module(
        "backend.02_features.09_featureflags.sub_features.02_permissions.repository"
    )
    async with pool.acquire() as conn:
        rank = await _repo.max_rank_for_user_on_flag(
            conn, user_id=user_id, flag_id=flag_id,
        )
    assert rank == 4  # admin

    # Cleanup lnk_user_roles + test user + test org
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "03_iam"."42_lnk_user_roles" WHERE user_id=$1', user_id,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id=3 AND entity_id=$1',
            user_id,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."12_fct_users" WHERE id=$1', user_id,
        )
        await conn.execute(
            "DELETE FROM \"04_audit\".\"60_evt_audit\" "
            "WHERE metadata->>'user_id'=$1",
            user_id,
        )
        await conn.execute(
            "DELETE FROM \"04_audit\".\"60_evt_audit\" WHERE metadata->>'org_id'=$1",
            ffp_org_id,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id=1 AND entity_id=$1',
            ffp_org_id,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."10_fct_orgs" WHERE id=$1', ffp_org_id,
        )


@pytest.mark.asyncio
async def test_grant_revoke_via_run_node(live_app) -> None:
    client, pool = live_app
    flag_id = await _make_flag(client, f"{_FLAG_PREFIX}delta")
    role_id = await _make_role(client, f"{_ROLE_CODE_PREFIX}ops")

    ctx_base = _ctx_mod.NodeContext(
        audit_category="setup", trace_id="t", span_id="s",
        extras={"pool": pool},
    )
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            result = await _catalog.run_node(
                pool, "featureflags.permissions.grant", ctx,
                {"role_id": role_id, "flag_id": flag_id, "permission": "toggle"},
            )
    grant = result["grant"]
    assert grant["permission"] == "toggle"

    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            out = await _catalog.run_node(
                pool, "featureflags.permissions.revoke", ctx,
                {"grant_id": grant["id"]},
            )
    assert out["grant_id"] == grant["id"]

"""
Integration tests for iam.memberships.
"""

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

_TEST_EMAIL_PREFIX = "itest-members-"
_TEST_ORG_SLUGS = ("itest-members-org-a",)
_TEST_WS_SLUGS = ("itest-members-ws-a",)


async def _cleanup_test_rows(pool: Any) -> None:
    async with pool.acquire() as conn:
        # Identify test users (by email prefix) + test orgs (by slug) + test workspaces.
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
        org_rows = await conn.fetch(
            'SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = ANY($1::text[])',
            list(_TEST_ORG_SLUGS),
        )
        org_ids = [r["id"] for r in org_rows]
        ws_rows = await conn.fetch(
            'SELECT id FROM "03_iam"."11_fct_workspaces" WHERE slug = ANY($1::text[])',
            list(_TEST_WS_SLUGS),
        )
        ws_ids = [r["id"] for r in ws_rows]

        # Delete membership rows first (FK safe).
        if user_ids or org_ids:
            await conn.execute(
                'DELETE FROM "03_iam"."40_lnk_user_orgs" '
                'WHERE user_id = ANY($1::text[]) OR org_id = ANY($2::text[])',
                user_ids or [""], org_ids or [""],
            )
        if user_ids or ws_ids:
            await conn.execute(
                'DELETE FROM "03_iam"."41_lnk_user_workspaces" '
                'WHERE user_id = ANY($1::text[]) OR workspace_id = ANY($2::text[])',
                user_ids or [""], ws_ids or [""],
            )
        # Audit rows for memberships tagged with any of our ids.
        await conn.execute(
            """
            DELETE FROM "04_audit"."60_evt_audit"
            WHERE event_key LIKE 'iam.memberships.%'
              AND (metadata->>'user_id' = ANY($1::text[])
                   OR metadata->>'org_id' = ANY($2::text[])
                   OR metadata->>'workspace_id' = ANY($3::text[]))
            """,
            user_ids or [""], org_ids or [""], ws_ids or [""],
        )
        # Users
        if user_ids:
            await conn.execute(
                """
                DELETE FROM "04_audit"."60_evt_audit"
                WHERE event_key LIKE 'iam.users.%'
                  AND metadata->>'user_id' = ANY($1::text[])
                """,
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" '
                'WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
                user_ids,
            )
        # Workspaces
        if ws_ids:
            await conn.execute(
                """
                DELETE FROM "04_audit"."60_evt_audit"
                WHERE event_key LIKE 'iam.workspaces.%'
                  AND metadata->>'workspace_id' = ANY($1::text[])
                """,
                ws_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" '
                'WHERE entity_type_id = 2 AND entity_id = ANY($1::text[])',
                ws_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."11_fct_workspaces" WHERE id = ANY($1::text[])',
                ws_ids,
            )
        # Orgs
        if org_ids:
            await conn.execute(
                """
                DELETE FROM "04_audit"."60_evt_audit"
                WHERE event_key LIKE 'iam.orgs.%'
                  AND metadata->>'org_id' = ANY($1::text[])
                """,
                org_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" '
                'WHERE entity_type_id = 1 AND entity_id = ANY($1::text[])',
                org_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."10_fct_orgs" WHERE id = ANY($1::text[])',
                org_ids,
            )


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup_test_rows(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac, pool
        finally:
            await _cleanup_test_rows(pool)
            _catalog.clear_checkers()


async def _create_org(client: AsyncClient, slug: str) -> str:
    r = await client.post("/v1/orgs", json={"slug": slug, "display_name": slug})
    assert r.status_code == 201
    return r.json()["data"]["id"]


async def _create_ws(client: AsyncClient, org_id: str, slug: str) -> str:
    r = await client.post(
        "/v1/workspaces",
        json={"org_id": org_id, "slug": slug, "display_name": slug},
    )
    assert r.status_code == 201
    return r.json()["data"]["id"]


async def _create_user(client: AsyncClient, email: str) -> str:
    r = await client.post(
        "/v1/users",
        json={
            "account_type": "email_password",
            "email": email,
            "display_name": email.split("@")[0],
        },
    )
    assert r.status_code == 201
    return r.json()["data"]["id"]


async def _count_events(pool: Any, event_key: str, **kw: str) -> int:
    async with pool.acquire() as conn:
        key, val = next(iter(kw.items()))
        return await conn.fetchval(
            'SELECT count(*) FROM "04_audit"."60_evt_audit" '
            f"WHERE event_key = $1 AND metadata->>'{key}' = $2",
            event_key, val,
        )


# ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_org_membership_assign_revoke(live_app) -> None:
    client, pool = live_app
    org_id = await _create_org(client, "itest-members-org-a")
    user_id = await _create_user(client, f"{_TEST_EMAIL_PREFIX}alice@example.com")

    # Assign
    r = await client.post(
        "/v1/org-members", json={"user_id": user_id, "org_id": org_id},
    )
    assert r.status_code == 201, r.text
    membership_id = r.json()["data"]["id"]
    assert await _count_events(pool, "iam.memberships.org.assigned", membership_id=membership_id) == 1

    # Dup
    r = await client.post(
        "/v1/org-members", json={"user_id": user_id, "org_id": org_id},
    )
    assert r.status_code == 409

    # List filters
    r = await client.get(f"/v1/org-members?user_id={user_id}")
    assert r.status_code == 200
    assert len(r.json()["data"]) == 1

    r = await client.get(f"/v1/org-members?org_id={org_id}")
    assert r.status_code == 200
    assert len(r.json()["data"]) == 1

    # Revoke
    r = await client.delete(f"/v1/org-members/{membership_id}")
    assert r.status_code == 204
    assert await _count_events(pool, "iam.memberships.org.revoked", membership_id=membership_id) == 1

    # Can re-assign after revoke
    r = await client.post(
        "/v1/org-members", json={"user_id": user_id, "org_id": org_id},
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_workspace_membership_assign_revoke(live_app) -> None:
    client, pool = live_app
    org_id = await _create_org(client, "itest-members-org-a")
    ws_id = await _create_ws(client, org_id, "itest-members-ws-a")
    user_id = await _create_user(client, f"{_TEST_EMAIL_PREFIX}bob@example.com")

    r = await client.post(
        "/v1/workspace-members",
        json={"user_id": user_id, "workspace_id": ws_id},
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["workspace_id"] == ws_id
    assert data["org_id"] == org_id  # derived from workspace
    membership_id = data["id"]
    assert await _count_events(pool, "iam.memberships.workspace.assigned", membership_id=membership_id) == 1

    r = await client.get(f"/v1/workspace-members?workspace_id={ws_id}")
    assert r.status_code == 200
    assert len(r.json()["data"]) == 1

    r = await client.delete(f"/v1/workspace-members/{membership_id}")
    assert r.status_code == 204
    assert await _count_events(pool, "iam.memberships.workspace.revoked", membership_id=membership_id) == 1


@pytest.mark.asyncio
async def test_membership_rejects_missing_parent(live_app) -> None:
    client, pool = live_app
    org_id = await _create_org(client, "itest-members-org-a")
    user_id = await _create_user(client, f"{_TEST_EMAIL_PREFIX}carol@example.com")
    missing_uuid = "00000000-0000-0000-0000-000000000000"

    # Unknown user
    r = await client.post(
        "/v1/org-members", json={"user_id": missing_uuid, "org_id": org_id},
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"

    # Unknown org
    r = await client.post(
        "/v1/org-members", json={"user_id": user_id, "org_id": missing_uuid},
    )
    assert r.status_code == 404

    # Unknown workspace
    r = await client.post(
        "/v1/workspace-members",
        json={"user_id": user_id, "workspace_id": missing_uuid},
    )
    assert r.status_code == 404

    # No rows inserted
    async with pool.acquire() as conn:
        lo = await conn.fetchval(
            'SELECT count(*) FROM "03_iam"."40_lnk_user_orgs" WHERE user_id = $1 OR org_id = $2',
            missing_uuid, missing_uuid,
        )
        lw = await conn.fetchval(
            'SELECT count(*) FROM "03_iam"."41_lnk_user_workspaces" WHERE workspace_id = $1',
            missing_uuid,
        )
    assert lo == 0
    assert lw == 0


@pytest.mark.asyncio
async def test_iam_memberships_nodes_via_run_node(live_app) -> None:
    client, pool = live_app
    org_id = await _create_org(client, "itest-members-org-a")
    ws_id = await _create_ws(client, org_id, "itest-members-ws-a")
    user_id = await _create_user(client, f"{_TEST_EMAIL_PREFIX}dave@example.com")

    ctx_base = _ctx_mod.NodeContext(
        audit_category="setup",
        trace_id="t", span_id="s",
        extras={"pool": pool},
    )

    # org.assign via run_node
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            result = await _catalog.run_node(
                pool, "iam.memberships.org.assign", ctx,
                {"user_id": user_id, "org_id": org_id},
            )
    m = result["membership"]
    assert m["user_id"] == user_id and m["org_id"] == org_id

    # workspace.assign via run_node (org_id auto-derived)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            result = await _catalog.run_node(
                pool, "iam.memberships.workspace.assign", ctx,
                {"user_id": user_id, "workspace_id": ws_id},
            )
    m = result["membership"]
    assert m["workspace_id"] == ws_id
    assert m["org_id"] == org_id

    # org.revoke via run_node
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            org_member_id = (await _catalog.run_node(
                pool, "iam.memberships.org.revoke", ctx,
                {"membership_id": m["id"] if False else (
                    # fetch the org membership id for this user/org
                    (await conn.fetchrow(
                        'SELECT id FROM "03_iam"."40_lnk_user_orgs" WHERE user_id=$1 AND org_id=$2',
                        user_id, org_id,
                    ))["id"]
                )},
            ))["membership_id"]
    assert org_member_id is not None

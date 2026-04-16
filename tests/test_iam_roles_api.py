"""Integration tests for iam.roles."""
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

_TEST_CODE_PREFIX = "itest_roles_"
_TEST_ORG_SLUGS = ("itest-roles-org-a",)


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS id FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 4 AND d.code = 'code' AND a.key_text LIKE $1
            """,
            f"{_TEST_CODE_PREFIX}%",
        )
        role_ids = [r["id"] for r in rows]
        org_rows = await conn.fetch(
            'SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = ANY($1::text[])',
            list(_TEST_ORG_SLUGS),
        )
        org_ids = [r["id"] for r in org_rows]

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
        if org_ids:
            await conn.execute(
                "DELETE FROM \"04_audit\".\"60_evt_audit\" "
                "WHERE event_key LIKE 'iam.orgs.%' AND metadata->>'org_id' = ANY($1::text[])",
                org_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id=1 AND entity_id = ANY($1::text[])',
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
        await _cleanup(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac, pool
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


async def _create_org(client: AsyncClient, slug: str) -> str:
    r = await client.post("/v1/orgs", json={"slug": slug, "display_name": slug})
    assert r.status_code == 201
    return r.json()["data"]["id"]


@pytest.mark.asyncio
async def test_role_crud_global_and_org_scoped(live_app) -> None:
    client, pool = live_app
    org_id = await _create_org(client, "itest-roles-org-a")

    # Global role (org_id=None)
    r = await client.post(
        "/v1/roles",
        json={"org_id": None, "role_type": "system", "code": f"{_TEST_CODE_PREFIX}admin", "label": "Admin"},
    )
    assert r.status_code == 201, r.text
    global_role_id = r.json()["data"]["id"]
    assert r.json()["data"]["org_id"] is None
    assert r.json()["data"]["role_type"] == "system"

    # Org-scoped role
    r = await client.post(
        "/v1/roles",
        json={"org_id": org_id, "role_type": "custom", "code": f"{_TEST_CODE_PREFIX}dev", "label": "Developer"},
    )
    assert r.status_code == 201
    org_role_id = r.json()["data"]["id"]

    # Dup (same org, same code)
    r = await client.post(
        "/v1/roles",
        json={"org_id": org_id, "role_type": "custom", "code": f"{_TEST_CODE_PREFIX}dev", "label": "Dup"},
    )
    assert r.status_code == 409

    # PATCH label
    r = await client.patch(f"/v1/roles/{global_role_id}", json={"label": "Admin v2"})
    assert r.status_code == 200
    assert r.json()["data"]["label"] == "Admin v2"

    # List filter by org_id
    r = await client.get(f"/v1/roles?org_id={org_id}")
    ids = [x["id"] for x in r.json()["data"]]
    assert org_role_id in ids
    assert global_role_id not in ids

    # DELETE
    r = await client.delete(f"/v1/roles/{global_role_id}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_role_invalid_role_type(live_app) -> None:
    client, _pool = live_app
    r = await client.post(
        "/v1/roles",
        json={"org_id": None, "role_type": "banana", "code": f"{_TEST_CODE_PREFIX}x", "label": "X"},
    )
    assert r.status_code == 422
    assert "role_type" in r.json()["error"]["message"]


@pytest.mark.asyncio
async def test_iam_roles_via_run_node(live_app) -> None:
    _client, pool = live_app
    ctx_base = _ctx_mod.NodeContext(
        audit_category="setup", trace_id="t", span_id="s",
        extras={"pool": pool},
    )
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            result = await _catalog.run_node(
                pool, "iam.roles.create", ctx,
                {"org_id": None, "role_type": "system", "code": f"{_TEST_CODE_PREFIX}node",
                 "label": "Node Role"},
            )
    role = result["role"]
    assert role["code"] == f"{_TEST_CODE_PREFIX}node"

    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            audit_category="system", trace_id="t2", span_id="s2",
            conn=conn, extras={"pool": pool},
        )
        got = await _catalog.run_node(pool, "iam.roles.get", ctx, {"id": role["id"]})
    assert got["role"]["id"] == role["id"]

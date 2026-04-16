"""Integration tests for iam.groups."""
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

_TEST_CODE_PREFIX = "itest_groups_"
_TEST_ORG_SLUGS = ("itest-groups-org-a", "itest-groups-org-b")


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS id FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 5 AND d.code = 'code' AND a.key_text LIKE $1
            """,
            f"{_TEST_CODE_PREFIX}%",
        )
        group_ids = [r["id"] for r in rows]
        org_rows = await conn.fetch(
            'SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = ANY($1::text[])',
            list(_TEST_ORG_SLUGS),
        )
        org_ids = [r["id"] for r in org_rows]

        if group_ids:
            await conn.execute(
                "DELETE FROM \"04_audit\".\"60_evt_audit\" WHERE event_key LIKE 'iam.groups.%' AND metadata->>'group_id' = ANY($1::text[])",
                group_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id=5 AND entity_id = ANY($1::text[])',
                group_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."14_fct_groups" WHERE id = ANY($1::text[])',
                group_ids,
            )
        if org_ids:
            await conn.execute(
                "DELETE FROM \"04_audit\".\"60_evt_audit\" WHERE event_key LIKE 'iam.orgs.%' AND metadata->>'org_id' = ANY($1::text[])",
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
async def test_group_crud_per_org_uniqueness(live_app) -> None:
    client, _pool = live_app
    org_a = await _create_org(client, "itest-groups-org-a")
    org_b = await _create_org(client, "itest-groups-org-b")

    r1 = await client.post(
        "/v1/groups",
        json={"org_id": org_a, "code": f"{_TEST_CODE_PREFIX}eng", "label": "Engineering"},
    )
    assert r1.status_code == 201
    g1_id = r1.json()["data"]["id"]

    # Same code, same org → 409
    r2 = await client.post(
        "/v1/groups",
        json={"org_id": org_a, "code": f"{_TEST_CODE_PREFIX}eng", "label": "Dup"},
    )
    assert r2.status_code == 409

    # Same code, different org → 201
    r3 = await client.post(
        "/v1/groups",
        json={"org_id": org_b, "code": f"{_TEST_CODE_PREFIX}eng", "label": "Eng B"},
    )
    assert r3.status_code == 201

    # GET one
    r = await client.get(f"/v1/groups/{g1_id}")
    assert r.status_code == 200
    assert r.json()["data"]["code"] == f"{_TEST_CODE_PREFIX}eng"

    # PATCH label
    r = await client.patch(f"/v1/groups/{g1_id}", json={"label": "Eng v2"})
    assert r.status_code == 200
    assert r.json()["data"]["label"] == "Eng v2"

    # DELETE
    r = await client.delete(f"/v1/groups/{g1_id}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_group_rejects_missing_org(live_app) -> None:
    client, _pool = live_app
    r = await client.post(
        "/v1/groups",
        json={"org_id": "00000000-0000-0000-0000-000000000000",
              "code": f"{_TEST_CODE_PREFIX}x", "label": "X"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_iam_groups_via_run_node(live_app) -> None:
    client, pool = live_app
    org_id = await _create_org(client, "itest-groups-org-a")

    ctx_base = _ctx_mod.NodeContext(
        audit_category="setup", trace_id="t", span_id="s",
        extras={"pool": pool},
    )
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            result = await _catalog.run_node(
                pool, "iam.groups.create", ctx,
                {"org_id": org_id, "code": f"{_TEST_CODE_PREFIX}node", "label": "Node Group"},
            )
    g = result["group"]
    assert g["code"] == f"{_TEST_CODE_PREFIX}node"
    assert g["org_id"] == org_id

    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            audit_category="system", trace_id="t2", span_id="s2",
            conn=conn, extras={"pool": pool},
        )
        got = await _catalog.run_node(pool, "iam.groups.get", ctx, {"id": g["id"]})
    assert got["group"]["id"] == g["id"]

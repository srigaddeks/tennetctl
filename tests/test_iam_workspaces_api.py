"""
Integration tests for iam.workspaces — second IAM vertical.

Covers:
  AC-1 — CRUD via HTTP + audit.
  AC-2 — per-org slug uniqueness (same slug allowed under different orgs).
  AC-3 — parent-org validation via run_node("iam.orgs.get", ...) returns 404.
  AC-4 — run_node("iam.workspaces.create", ...) — cross-sub-feature dispatch.
  AC-5 — run_node("iam.workspaces.get", ...) — control, no audit.
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

_TEST_ORG_SLUGS = ("itest-ws-org-a", "itest-ws-org-b")
_TEST_WS_SLUGS = ("itest-ws-crud", "itest-ws-dup", "itest-ws-node")


async def _cleanup_test_rows(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM "04_audit"."60_evt_audit"
            WHERE event_key LIKE 'iam.workspaces.%'
               OR (event_key LIKE 'iam.orgs.%'
                   AND (metadata->>'slug' = ANY($1::text[])
                        OR metadata->>'org_id' IN (
                            SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = ANY($1::text[])
                        )))
            """,
            list(_TEST_ORG_SLUGS),
        )
        await conn.execute(
            """
            DELETE FROM "03_iam"."41_lnk_user_workspaces"
            WHERE workspace_id IN (
                SELECT id FROM "03_iam"."11_fct_workspaces" WHERE slug = ANY($1::text[])
            )
            """,
            list(_TEST_WS_SLUGS),
        )
        await conn.execute(
            """
            DELETE FROM "03_iam"."21_dtl_attrs"
            WHERE entity_type_id = 2
              AND entity_id IN (
                  SELECT id FROM "03_iam"."11_fct_workspaces" WHERE slug = ANY($1::text[])
              )
            """,
            list(_TEST_WS_SLUGS),
        )
        await conn.execute(
            """
            DELETE FROM "03_iam"."21_dtl_attrs"
            WHERE entity_type_id = 1
              AND entity_id IN (
                  SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = ANY($1::text[])
              )
            """,
            list(_TEST_ORG_SLUGS),
        )
        await conn.execute(
            'DELETE FROM "03_iam"."11_fct_workspaces" WHERE slug = ANY($1::text[])',
            list(_TEST_WS_SLUGS),
        )
        await conn.execute(
            'DELETE FROM "03_iam"."10_fct_orgs" WHERE slug = ANY($1::text[])',
            list(_TEST_ORG_SLUGS),
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


async def _count_events(pool: Any, event_key: str, *, workspace_id: str | None = None, slug: str | None = None) -> int:
    async with pool.acquire() as conn:
        if workspace_id is not None:
            return await conn.fetchval(
                'SELECT count(*) FROM "04_audit"."60_evt_audit" '
                "WHERE event_key = $1 AND metadata->>'workspace_id' = $2",
                event_key, workspace_id,
            )
        return await conn.fetchval(
            'SELECT count(*) FROM "04_audit"."60_evt_audit" '
            "WHERE event_key = $1 AND metadata->>'slug' = $2",
            event_key, slug,
        )


async def _create_org_via_api(client: AsyncClient, slug: str) -> str:
    resp = await client.post(
        "/v1/orgs",
        json={"slug": slug, "display_name": f"Org {slug}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


# ─────────────────────────────────────────────────────────────────────
# AC-1: CRUD end-to-end
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_workspace_crud_end_to_end(live_app) -> None:
    client, pool = live_app
    org_id = await _create_org_via_api(client, "itest-ws-org-a")

    resp = await client.post(
        "/v1/workspaces",
        json={"org_id": org_id, "slug": "itest-ws-crud", "display_name": "Engineering"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    ws_id = data["id"]
    assert data["org_id"] == org_id
    assert data["slug"] == "itest-ws-crud"
    assert data["display_name"] == "Engineering"

    assert await _count_events(pool, "iam.workspaces.created", workspace_id=ws_id) == 1

    # GET one
    resp = await client.get(f"/v1/workspaces/{ws_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["org_id"] == org_id

    # List filtered by org_id — contains ws
    resp = await client.get(f"/v1/workspaces?org_id={org_id}")
    assert resp.status_code == 200
    payload = resp.json()
    slugs = [item["slug"] for item in payload["data"]]
    assert "itest-ws-crud" in slugs

    # List filtered by nonexistent org — empty
    resp = await client.get("/v1/workspaces?org_id=00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 200
    assert resp.json()["data"] == []

    # PATCH display_name
    resp = await client.patch(
        f"/v1/workspaces/{ws_id}",
        json={"display_name": "Engineering Ltd"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["display_name"] == "Engineering Ltd"
    assert await _count_events(pool, "iam.workspaces.updated", workspace_id=ws_id) == 1

    # No-op PATCH — no new audit row
    resp = await client.patch(
        f"/v1/workspaces/{ws_id}",
        json={"display_name": "Engineering Ltd"},
    )
    assert resp.status_code == 200
    assert await _count_events(pool, "iam.workspaces.updated", workspace_id=ws_id) == 1

    # DELETE
    resp = await client.delete(f"/v1/workspaces/{ws_id}")
    assert resp.status_code == 204
    assert resp.text == ""
    assert await _count_events(pool, "iam.workspaces.deleted", workspace_id=ws_id) == 1

    # GET after delete → 404
    resp = await client.get(f"/v1/workspaces/{ws_id}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


# ─────────────────────────────────────────────────────────────────────
# AC-2: Per-org slug uniqueness
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_workspace_slug_conflict_per_org(live_app) -> None:
    client, pool = live_app
    org_a = await _create_org_via_api(client, "itest-ws-org-a")
    org_b = await _create_org_via_api(client, "itest-ws-org-b")

    # First workspace under org A
    r1 = await client.post(
        "/v1/workspaces",
        json={"org_id": org_a, "slug": "itest-ws-dup", "display_name": "Dup A"},
    )
    assert r1.status_code == 201

    # Duplicate (org_a, slug) → 409
    r2 = await client.post(
        "/v1/workspaces",
        json={"org_id": org_a, "slug": "itest-ws-dup", "display_name": "Dup again"},
    )
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "CONFLICT"

    # Same slug under org B → 201 (per-org scope proves uniqueness is compound)
    r3 = await client.post(
        "/v1/workspaces",
        json={"org_id": org_b, "slug": "itest-ws-dup", "display_name": "Dup B"},
    )
    assert r3.status_code == 201

    async with pool.acquire() as conn:
        count = await conn.fetchval(
            'SELECT count(*) FROM "03_iam"."11_fct_workspaces" WHERE slug = $1',
            "itest-ws-dup",
        )
    assert count == 2


# ─────────────────────────────────────────────────────────────────────
# AC-3: Parent-org validation via run_node("iam.orgs.get", ...)
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_workspace_create_rejected_when_org_missing(live_app) -> None:
    client, pool = live_app
    missing = "00000000-0000-0000-0000-000000000000"

    resp = await client.post(
        "/v1/workspaces",
        json={"org_id": missing, "slug": "itest-ws-node", "display_name": "Orphan"},
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "NOT_FOUND"
    assert missing in body["error"]["message"]

    # Nothing persisted
    async with pool.acquire() as conn:
        ws_rows = await conn.fetchval(
            'SELECT count(*) FROM "03_iam"."11_fct_workspaces" WHERE slug = $1',
            "itest-ws-node",
        )
        events = await conn.fetchval(
            'SELECT count(*) FROM "04_audit"."60_evt_audit" '
            "WHERE event_key = 'iam.workspaces.created' AND metadata->>'slug' = $1",
            "itest-ws-node",
        )
    assert ws_rows == 0
    assert events == 0


# ─────────────────────────────────────────────────────────────────────
# AC-4 + AC-5: run_node cross-sub-feature dispatch
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_iam_workspaces_create_and_get_via_run_node(live_app) -> None:
    client, pool = live_app
    org_id = await _create_org_via_api(client, "itest-ws-org-a")

    ctx_base = _ctx_mod.NodeContext(
        audit_category="setup",
        trace_id="trace-ws-rn",
        span_id="span-ws-rn",
        extras={"pool": pool},
    )

    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            result = await _catalog.run_node(
                pool, "iam.workspaces.create", ctx,
                {"org_id": org_id, "slug": "itest-ws-node", "display_name": "Via Node"},
            )
    assert "workspace" in result
    ws = result["workspace"]
    ws_id = ws["id"]
    assert ws["org_id"] == org_id
    assert ws["slug"] == "itest-ws-node"
    assert ws["display_name"] == "Via Node"

    assert await _count_events(pool, "iam.workspaces.created", workspace_id=ws_id) == 1

    # iam.workspaces.get — control, no audit
    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            audit_category="system",
            trace_id="t1", span_id="s1",
            conn=conn,
            extras={"pool": pool},
        )
        got = await _catalog.run_node(pool, "iam.workspaces.get", ctx, {"id": ws_id})
    assert got["workspace"] is not None
    assert got["workspace"]["id"] == ws_id

    # Missing id → None
    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            audit_category="system",
            trace_id="t2", span_id="s2",
            conn=conn,
            extras={"pool": pool},
        )
        missing = await _catalog.run_node(
            pool, "iam.workspaces.get", ctx,
            {"id": "00000000-0000-0000-0000-000000000000"},
        )
    assert missing == {"workspace": None}

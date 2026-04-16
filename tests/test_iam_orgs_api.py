"""
Integration tests for iam.orgs — the first real IAM vertical.

Covers:
  AC-1 + AC-2 — CRUD via HTTP + slug conflict envelope + audit assertions.
  AC-3 — iam.orgs.create via run_node (cross-sub-feature dispatch).
  AC-4 — iam.orgs.get via run_node (control, no audit).

Runs against the LIVE tennetctl database (same pattern as test_audit_emit_node.py
and test_iam_views.py). The 03_iam schema lives there; test DB doesn't have it.
Each test cleans up the fct / dtl / evt rows it creates.
"""

from __future__ import annotations

import os
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

_TEST_SLUGS = ("itest-orgs-crud", "itest-orgs-dup", "itest-orgs-via-node")


async def _cleanup_test_rows(pool: Any) -> None:
    """Remove all rows created by these tests — runs in setup + teardown."""
    async with pool.acquire() as conn:
        # 1. Audit rows referencing the test slugs (use metadata.slug OR metadata.org_id).
        await conn.execute(
            """
            DELETE FROM "04_audit"."60_evt_audit"
            WHERE event_key LIKE 'iam.orgs.%'
              AND (metadata->>'slug' = ANY($1::text[])
                   OR metadata->>'org_id' IN (
                       SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = ANY($1::text[])
                   ))
            """,
            list(_TEST_SLUGS),
        )
        # 2. dtl_attrs rows for orgs with test slugs.
        await conn.execute(
            """
            DELETE FROM "03_iam"."21_dtl_attrs"
            WHERE entity_type_id = 1
              AND entity_id IN (
                  SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = ANY($1::text[])
              )
            """,
            list(_TEST_SLUGS),
        )
        # 3. fct_orgs rows with test slugs.
        await conn.execute(
            'DELETE FROM "03_iam"."10_fct_orgs" WHERE slug = ANY($1::text[])',
            list(_TEST_SLUGS),
        )


@pytest.fixture
async def live_app():
    """
    Boot the FastAPI app against the live DB (pool + catalog upsert via lifespan),
    yield an httpx ASGI client, tear down on exit.

    Cleans up any lingering test rows at both ends so reruns stay hermetic.
    """
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


async def _count_events(pool: Any, event_key: str, slug: str) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            SELECT count(*) FROM "04_audit"."60_evt_audit"
            WHERE event_key = $1
              AND (metadata->>'slug' = $2
                   OR metadata->>'org_id' IN (
                       SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = $2
                   ))
            """,
            event_key, slug,
        )


async def _fetch_org_row(pool: Any, slug: str) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT id, slug, deleted_at FROM "03_iam"."10_fct_orgs" WHERE slug = $1',
            slug,
        )
        return dict(row) if row else None


async def _fetch_display_name(pool: Any, org_id: str) -> str | None:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            'SELECT display_name FROM "03_iam"."v_orgs" WHERE id = $1',
            org_id,
        )


# ─────────────────────────────────────────────────────────────────────
# AC-1 + AC-5: full CRUD + audit + router mount
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_org_crud_end_to_end(live_app) -> None:
    client, pool = live_app
    slug = "itest-orgs-crud"

    # POST — create
    resp = await client.post(
        "/v1/orgs",
        json={"slug": slug, "display_name": "Integration CRUD"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["ok"] is True
    created = body["data"]
    org_id = created["id"]
    assert created["slug"] == slug
    assert created["display_name"] == "Integration CRUD"
    assert created["is_active"] is True
    assert created["created_by"] == "sys"

    # DB assertions — fct row + dtl display_name + audit event
    row = await _fetch_org_row(pool, slug)
    assert row is not None
    assert row["id"] == org_id
    assert row["deleted_at"] is None
    assert await _fetch_display_name(pool, org_id) == "Integration CRUD"
    assert await _count_events(pool, "iam.orgs.created", slug) == 1

    # GET one
    resp = await client.get(f"/v1/orgs/{org_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["slug"] == slug
    assert resp.json()["data"]["display_name"] == "Integration CRUD"

    # GET list — should contain our org
    resp = await client.get("/v1/orgs")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["ok"] is True
    assert payload["pagination"]["total"] >= 1
    slugs = [item["slug"] for item in payload["data"]]
    assert slug in slugs

    # PATCH — update display_name
    resp = await client.patch(
        f"/v1/orgs/{org_id}",
        json={"display_name": "Integration CRUD v2"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["display_name"] == "Integration CRUD v2"
    assert await _fetch_display_name(pool, org_id) == "Integration CRUD v2"
    assert await _count_events(pool, "iam.orgs.updated", slug) == 1

    # PATCH with no real change should not emit another audit event
    resp = await client.patch(
        f"/v1/orgs/{org_id}",
        json={"display_name": "Integration CRUD v2"},
    )
    assert resp.status_code == 200
    assert await _count_events(pool, "iam.orgs.updated", slug) == 1

    # DELETE — soft delete
    resp = await client.delete(f"/v1/orgs/{org_id}")
    assert resp.status_code == 204
    assert resp.text == ""
    row = await _fetch_org_row(pool, slug)
    assert row is not None
    assert row["deleted_at"] is not None
    assert await _count_events(pool, "iam.orgs.deleted", slug) == 1

    # GET after delete — 404 with envelope
    resp = await client.get(f"/v1/orgs/{org_id}")
    assert resp.status_code == 404
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "NOT_FOUND"


# ─────────────────────────────────────────────────────────────────────
# AC-2: slug uniqueness
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_org_slug_conflict(live_app) -> None:
    client, pool = live_app
    slug = "itest-orgs-dup"

    resp = await client.post("/v1/orgs", json={"slug": slug, "display_name": "First"})
    assert resp.status_code == 201

    resp = await client.post("/v1/orgs", json={"slug": slug, "display_name": "Second"})
    assert resp.status_code == 409
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "CONFLICT"
    assert slug in body["error"]["message"]

    # Exactly one row for the slug + exactly one created-event.
    async with pool.acquire() as conn:
        count = await conn.fetchval(
            'SELECT count(*) FROM "03_iam"."10_fct_orgs" WHERE slug = $1',
            slug,
        )
    assert count == 1
    assert await _count_events(pool, "iam.orgs.created", slug) == 1


# ─────────────────────────────────────────────────────────────────────
# AC-3 + AC-4: run_node dispatch for cross-sub-feature callers
# ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_iam_orgs_create_and_get_via_run_node(live_app) -> None:
    _client, pool = live_app
    slug = "itest-orgs-via-node"

    ctx_base = _ctx_mod.NodeContext(
        audit_category="setup",
        user_id=None, session_id=None, org_id=None, workspace_id=None,
        trace_id="trace-iam-orgs-rn",
        span_id="span-iam-orgs-rn",
        extras={"pool": pool},
    )

    # iam.orgs.create — tx=caller, so we open a tx and attach conn to ctx.
    async with pool.acquire() as conn:
        async with conn.transaction():
            from dataclasses import replace
            ctx = replace(ctx_base, conn=conn)
            result = await _catalog.run_node(
                pool, "iam.orgs.create", ctx,
                {"slug": slug, "display_name": "Via Node"},
            )
    assert "org" in result
    org = result["org"]
    org_id = org["id"]
    assert org["slug"] == slug
    assert org["display_name"] == "Via Node"

    # DB + audit assertions
    row = await _fetch_org_row(pool, slug)
    assert row is not None and row["id"] == org_id
    assert await _fetch_display_name(pool, org_id) == "Via Node"
    assert await _count_events(pool, "iam.orgs.created", slug) == 1

    # iam.orgs.get — control kind, does not emit audit
    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            audit_category="system",
            trace_id="trace-get-1", span_id="span-get-1",
            conn=conn,
            extras={"pool": pool},
        )
        got = await _catalog.run_node(pool, "iam.orgs.get", ctx, {"id": org_id})
    assert got["org"] is not None
    assert got["org"]["id"] == org_id
    assert got["org"]["slug"] == slug

    # Missing id returns org=None (no 404 — that's an HTTP concern).
    async with pool.acquire() as conn:
        ctx = _ctx_mod.NodeContext(
            audit_category="system",
            trace_id="trace-get-2", span_id="span-get-2",
            conn=conn,
            extras={"pool": pool},
        )
        missing = await _catalog.run_node(
            pool, "iam.orgs.get", ctx, {"id": "00000000-0000-0000-0000-000000000000"},
        )
    assert missing == {"org": None}

    # Confirm no audit event was emitted by the two get calls.
    async with pool.acquire() as conn:
        get_events = await conn.fetchval(
            """
            SELECT count(*) FROM "04_audit"."60_evt_audit"
            WHERE event_key = 'iam.orgs.get'
               OR metadata->>'org_id' = $1 AND event_key LIKE 'iam.orgs.get%'
            """,
            org_id,
        )
    assert get_events == 0

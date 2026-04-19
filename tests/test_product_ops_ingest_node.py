"""
Integration tests for product_ops.events.ingest — runs against live Postgres.

Requires:
  - DATABASE_URL env (or default at port 5434)
  - Schema "10_product_ops" applied (run migrator UP first)
  - A vault entry at "product_ops/project_keys/{TEST_PROJECT_KEY}" containing
    {"org_id": "<test-org>", "workspace_id": "<test-workspace>"}

Tests skip if vault setup is not present so the suite stays portable.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

import pytest

_catalog: Any = import_module("backend.01_catalog")
_ctx_mod: Any = import_module("backend.01_catalog.context")
_db: Any = import_module("backend.01_core.database")
_core_id: Any = import_module("backend.01_core.id")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

TEST_PROJECT_KEY = os.environ.get("TEST_PROJECT_KEY", "pk_test_product_ops")
TEST_ORG_ID = os.environ.get("TEST_ORG_ID", "00000000-0000-0000-0000-000000000001")
TEST_WS_ID = os.environ.get("TEST_WORKSPACE_ID", "00000000-0000-0000-0000-000000000002")

MODULES = frozenset({"core", "iam", "audit", "vault", "product_ops"})


pytestmark = pytest.mark.asyncio


async def _provision_vault_project_key(pool: Any, ctx: Any) -> bool:
    """Create the vault entry the service will look up. Returns False on failure."""
    try:
        await _catalog.run_node(
            pool, "vault.secrets.put",
            ctx,
            {
                "key": f"product_ops/project_keys/{TEST_PROJECT_KEY}",
                "plaintext": json.dumps({"org_id": TEST_ORG_ID, "workspace_id": TEST_WS_ID}),
            },
        )
        return True
    except Exception:
        return False


async def _check_schema_applied(pool: Any) -> bool:
    async with pool.acquire() as conn:
        return bool(await conn.fetchval(
            "SELECT to_regclass('\"10_product_ops\".\"60_evt_product_events\"')"
        ))


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "10_product_ops"."60_evt_product_events" WHERE workspace_id = $1',
            TEST_WS_ID,
        )
        await conn.execute(
            'DELETE FROM "10_product_ops"."60_evt_attribution_touches" WHERE workspace_id = $1',
            TEST_WS_ID,
        )
        await conn.execute(
            'DELETE FROM "10_product_ops"."10_fct_visitors" WHERE workspace_id = $1',
            TEST_WS_ID,
        )
        await conn.execute(
            'DELETE FROM "04_audit"."60_evt_audit" WHERE event_key = $1',
            "product_ops.events.ingested",
        )


@pytest.fixture
async def pool():
    pool = await _db.create_pool(LIVE_DSN)
    try:
        if not await _check_schema_applied(pool):
            pytest.skip("10_product_ops schema not applied — run migrator UP first")
        await _catalog.upsert_all(pool, MODULES)
        ctx = _ctx_mod.NodeContext.system()
        if not await _provision_vault_project_key(pool, ctx):
            pytest.skip("Could not provision vault project key — vault.secrets.put unavailable")
        yield pool
        await _cleanup(pool)
    finally:
        await pool.close()


def _ev(**overrides) -> dict:
    base = {
        "kind": "page_view",
        "anonymous_id": "v_test_" + _core_id.uuid7()[:8],
        "occurred_at": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return base


# ── Happy path ──────────────────────────────────────────────────────

async def test_single_page_view_lands(pool):
    ev = _ev()
    res = await _catalog.run_node(
        pool, "product_ops.events.ingest", _ctx_mod.NodeContext.system(),
        {
            "project_key": TEST_PROJECT_KEY,
            "events": [ev],
            "client_ip": "203.0.113.42",
        },
    )
    assert res["accepted"] == 1
    assert res["dropped_dnt"] == 0

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT visitor_id, page_url, metadata FROM "10_product_ops"."60_evt_product_events" '
            'WHERE workspace_id = $1 ORDER BY occurred_at DESC LIMIT 1',
            TEST_WS_ID,
        )
        assert row is not None
        # IP truncation observable in metadata
        assert row["metadata"].get("_ip_truncated", "").startswith("203.0.113")


async def test_dnt_drops_all_events(pool):
    ev = _ev()
    res = await _catalog.run_node(
        pool, "product_ops.events.ingest", _ctx_mod.NodeContext.system(),
        {
            "project_key": TEST_PROJECT_KEY,
            "events": [ev],
            "dnt": True,
        },
    )
    assert res["accepted"] == 0
    assert res["dropped_dnt"] == 1

    async with pool.acquire() as conn:
        cnt = await conn.fetchval(
            'SELECT COUNT(*) FROM "10_product_ops"."60_evt_product_events" '
            'WHERE workspace_id = $1',
            TEST_WS_ID,
        )
        assert cnt == 0


async def test_utm_extracted_from_page_url(pool):
    url = "https://example.com/landing?utm_source=twitter&utm_campaign=launch"
    ev = _ev(page_url=url, referrer="https://t.co/xyz")
    res = await _catalog.run_node(
        pool, "product_ops.events.ingest", _ctx_mod.NodeContext.system(),
        {"project_key": TEST_PROJECT_KEY, "events": [ev]},
    )
    assert res["accepted"] == 1

    async with pool.acquire() as conn:
        v = await conn.fetchrow(
            'SELECT first_utm_campaign, first_referrer FROM "10_product_ops"."10_fct_visitors" '
            'WHERE workspace_id = $1 AND anonymous_id = $2',
            TEST_WS_ID, ev["anonymous_id"],
        )
        assert v is not None
        assert v["first_utm_campaign"] == "launch"
        assert v["first_referrer"] == "https://t.co/xyz"

        touch_count = await conn.fetchval(
            'SELECT COUNT(*) FROM "10_product_ops"."60_evt_attribution_touches" '
            'WHERE workspace_id = $1',
            TEST_WS_ID,
        )
        assert touch_count == 1


async def test_one_audit_row_per_batch_not_per_event(pool):
    """ADR-030 hot-path bypass: one audit summary per batch."""
    events = [_ev(anonymous_id=f"v_batch_{i}") for i in range(5)]
    await _catalog.run_node(
        pool, "product_ops.events.ingest", _ctx_mod.NodeContext.system(),
        {"project_key": TEST_PROJECT_KEY, "events": events},
    )

    async with pool.acquire() as conn:
        audit_count = await conn.fetchval(
            'SELECT COUNT(*) FROM "04_audit"."60_evt_audit" '
            "WHERE event_key = 'product_ops.events.ingested'",
        )
        # Exactly 1 audit row, not 5.
        assert audit_count == 1


async def test_visitor_dedupe_within_batch(pool):
    """Two events with same anonymous_id → one fct_visitors row, two events."""
    aid = "v_dedupe_" + _core_id.uuid7()[:8]
    events = [
        _ev(anonymous_id=aid, kind="page_view"),
        _ev(anonymous_id=aid, kind="custom", event_name="cta_click"),
    ]
    res = await _catalog.run_node(
        pool, "product_ops.events.ingest", _ctx_mod.NodeContext.system(),
        {"project_key": TEST_PROJECT_KEY, "events": events},
    )
    assert res["accepted"] == 2

    async with pool.acquire() as conn:
        v_count = await conn.fetchval(
            'SELECT COUNT(*) FROM "10_product_ops"."10_fct_visitors" WHERE anonymous_id = $1',
            aid,
        )
        assert v_count == 1
        e_count = await conn.fetchval(
            'SELECT COUNT(*) FROM "10_product_ops"."60_evt_product_events" '
            'WHERE workspace_id = $1 AND visitor_id = '
            '(SELECT id FROM "10_product_ops"."10_fct_visitors" WHERE anonymous_id = $2)',
            TEST_WS_ID, aid,
        )
        assert e_count == 2

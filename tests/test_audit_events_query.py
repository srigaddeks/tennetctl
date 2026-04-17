"""
Integration tests for audit.events query path (Phase 10 Plan 01).

Runs against the LIVE tennetctl DB. Seeds ~50 rows via the canonical emit node
(audit.events.emit) so tests exercise the same write path consumers use.

Covers:
  AC-2 — list with filters + cursor pagination.
  AC-3 — detail + stats (hour/day buckets) + registered-keys.
  AC-4 — audit.events.query node (shape equality + no-audit-emit).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_ctx_mod: Any = import_module("backend.01_catalog.context")
_repo: Any = import_module(
    "backend.02_features.04_audit.sub_features.01_events.repository"
)

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

# Every seeded row carries event_key prefix 'qtest.' for easy cleanup.
_SEED_PREFIX = "qtest."
_SEED_ORG_A = "qtest-org-a"
_SEED_ORG_B = "qtest-org-b"
_SEED_USER_A = "qtest-user-a"
_SEED_USER_B = "qtest-user-b"
_SEED_SESSION = "qtest-session"
_SEED_WORKSPACE = "qtest-workspace"
_SEED_TRACE_A = "qtest-trace-a"
_SEED_TRACE_B = "qtest-trace-b"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "04_audit"."60_evt_audit" WHERE event_key LIKE $1',
            _SEED_PREFIX + "%",
        )
        await conn.execute(
            'DELETE FROM "04_audit"."02_dim_audit_event_keys" WHERE key LIKE $1',
            _SEED_PREFIX + "%",
        )


def _make_ctx(
    *,
    org_id: str | None = _SEED_ORG_A,
    user_id: str | None = _SEED_USER_A,
    trace_id: str = _SEED_TRACE_A,
    category: str = "user",
) -> Any:
    return _ctx_mod.NodeContext(
        user_id=user_id,
        session_id=_SEED_SESSION,
        org_id=org_id,
        workspace_id=_SEED_WORKSPACE,
        trace_id=trace_id,
        span_id="qtest-span",
        parent_span_id=None,
        audit_category=category,
    )


async def _seed_50_events(pool: Any) -> list[str]:
    """
    Seed 50 events:
      5 event_keys × (2 orgs × 2 users × 2 outcomes) + filler
    Returns the event_ids written.
    """
    event_keys = [
        f"{_SEED_PREFIX}orgs.created",
        f"{_SEED_PREFIX}orgs.updated",
        f"{_SEED_PREFIX}users.signed_up",
        f"{_SEED_PREFIX}users.logged_in",
        f"{_SEED_PREFIX}billing.charged",
    ]
    orgs = [_SEED_ORG_A, _SEED_ORG_B]
    users = [_SEED_USER_A, _SEED_USER_B]
    outcomes = ["success", "failure"]
    ids: list[str] = []
    for k in event_keys:
        for o in orgs:
            for u in users:
                for oc in outcomes:
                    # user-category + success needs full scope; failure bypasses.
                    ctx = _make_ctx(org_id=o, user_id=u, category="user")
                    result = await _catalog.run_node(
                        pool,
                        "audit.events.emit",
                        ctx,
                        {"event_key": k, "outcome": oc, "metadata": {"k": k, "o": o, "u": u}},
                    )
                    ids.append(result["audit_id"])
                    # 2 * 2 * 2 = 8 per key, 5 keys → 40. Add 10 filler rows below.
    # Filler: 10 integration-category rows, different trace_id
    for i in range(10):
        ctx = _make_ctx(
            org_id=_SEED_ORG_A,
            user_id=_SEED_USER_A,
            trace_id=_SEED_TRACE_B,
            category="integration",
        )
        result = await _catalog.run_node(
            pool,
            "audit.events.emit",
            ctx,
            {
                "event_key": f"{_SEED_PREFIX}webhook.received",
                "outcome": "success",
                "metadata": {"i": i, "note": "special-filler"},
            },
        )
        ids.append(result["audit_id"])
    return ids


@pytest.fixture
async def seeded():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        ids = await _seed_50_events(pool)
        transport = ASGITransport(app=_main.app)
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac, pool, ids
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


# ─── list + pagination ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_no_filters_returns_items_and_cursor(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}*", "limit": 10},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    data = body["data"]
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 10
    assert data["next_cursor"] is not None


@pytest.mark.asyncio
async def test_cursor_pagination_no_duplicates_no_gaps(seeded) -> None:
    client, _, ids = seeded
    collected: list[str] = []
    cursor: str | None = None
    while True:
        params: dict = {"event_key": f"{_SEED_PREFIX}*", "limit": 10}
        if cursor:
            params["cursor"] = cursor
        resp = await client.get("/v1/audit-events", params=params)
        assert resp.status_code == 200
        data = resp.json()["data"]
        collected.extend([row["id"] for row in data["items"]])
        cursor = data["next_cursor"]
        if cursor is None:
            break
    assert len(collected) == 50
    assert len(set(collected)) == 50
    assert set(collected) == set(ids)


# ─── filters ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_filter_by_event_key_exact(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}orgs.created", "limit": 1000},
    )
    items = resp.json()["data"]["items"]
    assert len(items) == 8
    assert all(r["event_key"] == f"{_SEED_PREFIX}orgs.created" for r in items)


@pytest.mark.asyncio
async def test_filter_by_event_key_glob(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}orgs.*", "limit": 1000},
    )
    items = resp.json()["data"]["items"]
    keys = {r["event_key"] for r in items}
    assert keys == {f"{_SEED_PREFIX}orgs.created", f"{_SEED_PREFIX}orgs.updated"}


@pytest.mark.asyncio
async def test_filter_by_outcome_failure(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}*", "outcome": "failure", "limit": 1000},
    )
    items = resp.json()["data"]["items"]
    # 5 keys × 2 orgs × 2 users × 1 outcome = 20
    assert len(items) == 20
    assert all(r["outcome"] == "failure" for r in items)


@pytest.mark.asyncio
async def test_filter_by_category_integration(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}*", "category_code": "integration", "limit": 1000},
    )
    items = resp.json()["data"]["items"]
    assert len(items) == 10
    assert all(r["category_code"] == "integration" for r in items)


@pytest.mark.asyncio
async def test_filter_by_org_id(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}*", "org_id": _SEED_ORG_B, "limit": 1000},
    )
    items = resp.json()["data"]["items"]
    assert all(r["org_id"] == _SEED_ORG_B for r in items)
    # 5 user-category keys × 1 org × 2 users × 2 outcomes = 20
    assert len(items) == 20


@pytest.mark.asyncio
async def test_filter_by_actor_user_id(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}*", "actor_user_id": _SEED_USER_B, "limit": 1000},
    )
    items = resp.json()["data"]["items"]
    assert all(r["actor_user_id"] == _SEED_USER_B for r in items)


@pytest.mark.asyncio
async def test_filter_by_trace_id(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}*", "trace_id": _SEED_TRACE_B, "limit": 1000},
    )
    items = resp.json()["data"]["items"]
    assert len(items) == 10
    assert all(r["trace_id"] == _SEED_TRACE_B for r in items)


@pytest.mark.asyncio
async def test_filter_by_time_range(seeded) -> None:
    client, _, _ = seeded
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # All 50 seeded rows were created seconds ago — an until in the past returns 0.
    until_past = (now - timedelta(hours=1)).isoformat()
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}*", "until": until_past, "limit": 1000},
    )
    assert resp.json()["data"]["items"] == []

    since_past = (now - timedelta(hours=1)).isoformat()
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}*", "since": since_past, "limit": 1000},
    )
    assert len(resp.json()["data"]["items"]) == 50


@pytest.mark.asyncio
async def test_filter_combination_intersects(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events",
        params={
            "event_key": f"{_SEED_PREFIX}orgs.*",
            "outcome": "success",
            "org_id": _SEED_ORG_A,
            "limit": 1000,
        },
    )
    items = resp.json()["data"]["items"]
    # 2 orgs.* keys × 1 org × 2 users × 1 outcome = 4
    assert len(items) == 4
    for r in items:
        assert r["event_key"].startswith(f"{_SEED_PREFIX}orgs.")
        assert r["outcome"] == "success"
        assert r["org_id"] == _SEED_ORG_A


@pytest.mark.asyncio
async def test_filter_metadata_substring(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}*", "q": "special-filler", "limit": 1000},
    )
    items = resp.json()["data"]["items"]
    assert len(items) == 10
    assert all("special-filler" in str(r["metadata"]) for r in items)


# ─── detail ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_event_by_id_returns_detail(seeded) -> None:
    client, _, ids = seeded
    eid = ids[0]
    resp = await client.get(f"/v1/audit-events/{eid}")
    assert resp.status_code == 200
    row = resp.json()["data"]
    assert row["id"] == eid
    assert row["category_label"] == "User"  # resolved via view join
    assert "trace_id" in row


@pytest.mark.asyncio
async def test_get_event_by_id_404_on_unknown(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get("/v1/audit-events/019d974e-1eab-7952-be74-000000000000")
    assert resp.status_code == 404


# ─── stats ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stats_hourly_buckets_and_aggregates(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events/stats",
        params={"event_key": f"{_SEED_PREFIX}*", "bucket": "hour"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]

    key_counts = {row["event_key"]: row["count"] for row in data["by_event_key"]}
    assert key_counts[f"{_SEED_PREFIX}orgs.created"] == 8

    outcome_counts = {row["outcome"]: row["count"] for row in data["by_outcome"]}
    # 40 user rows (20 success + 20 failure) + 10 integration success = 30 success / 20 failure
    assert outcome_counts["success"] == 30
    assert outcome_counts["failure"] == 20

    cat_counts = {row["category_code"]: row["count"] for row in data["by_category"]}
    assert cat_counts["user"] == 40
    assert cat_counts["integration"] == 10

    assert len(data["time_series"]) >= 1
    assert sum(row["count"] for row in data["time_series"]) == 50


@pytest.mark.asyncio
async def test_stats_daily_bucket(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events/stats",
        params={"event_key": f"{_SEED_PREFIX}*", "bucket": "day"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert sum(row["count"] for row in data["time_series"]) == 50


# ─── registered keys ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_event_keys_returns_registered(seeded) -> None:
    client, pool, _ = seeded
    # Register a key via the service upsert helper
    async with pool.acquire() as conn:
        await _repo.upsert_event_key(
            conn,
            key=f"{_SEED_PREFIX}orgs.created",
            label="Org Created (test)",
            description="A test org was created.",
            category_code="user",
        )
    resp = await client.get("/v1/audit-event-keys")
    assert resp.status_code == 200
    data = resp.json()["data"]
    keys = {row["key"] for row in data["items"]}
    assert f"{_SEED_PREFIX}orgs.created" in keys
    assert data["total"] == len(data["items"])


# ─── query node (shape equality + no-audit-emit) ─────────────────────


@pytest.mark.asyncio
async def test_query_node_returns_same_shape_as_http(seeded) -> None:
    client, pool, _ = seeded
    # HTTP
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}orgs.*", "limit": 5},
    )
    http_items = resp.json()["data"]["items"]

    # Node — tx=caller requires ctx.conn
    conn = await asyncpg.connect(LIVE_DSN)
    try:
        from dataclasses import replace
        ctx_base = _make_ctx(category="system")
        ctx = replace(ctx_base, conn=conn)
        result = await _catalog.run_node(
            pool,
            "audit.events.query",
            ctx,
            {"event_key": f"{_SEED_PREFIX}orgs.*", "limit": 5},
        )
    finally:
        await conn.close()

    node_items = result["items"]
    assert len(node_items) == len(http_items)
    assert {r["id"] for r in node_items} == {r["id"] for r in http_items}


@pytest.mark.asyncio
async def test_query_node_does_not_emit_audit(seeded) -> None:
    _, pool, _ = seeded
    async with pool.acquire() as c:
        before = await c.fetchval(
            'SELECT count(*) FROM "04_audit"."60_evt_audit" WHERE event_key LIKE $1',
            _SEED_PREFIX + "%",
        )

    conn = await asyncpg.connect(LIVE_DSN)
    try:
        from dataclasses import replace
        ctx_base = _make_ctx(category="system")
        ctx = replace(ctx_base, conn=conn)
        await _catalog.run_node(
            pool,
            "audit.events.query",
            ctx,
            {"event_key": f"{_SEED_PREFIX}*", "limit": 10},
        )
    finally:
        await conn.close()

    async with pool.acquire() as c:
        after = await c.fetchval(
            'SELECT count(*) FROM "04_audit"."60_evt_audit" WHERE event_key LIKE $1',
            _SEED_PREFIX + "%",
        )
    assert before == after, "audit.events.query must not emit audit events"


# ─── authz (cross-org rejection) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_authz_rejects_cross_org_list_when_session_scoped(seeded) -> None:
    client, _, _ = seeded
    # Session header bound to org_A; filter asks for org_B → 403.
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}*", "org_id": _SEED_ORG_B, "limit": 10},
        headers={"x-org-id": _SEED_ORG_A},
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_authz_forces_session_org_when_filter_missing(seeded) -> None:
    client, _, _ = seeded
    resp = await client.get(
        "/v1/audit-events",
        params={"event_key": f"{_SEED_PREFIX}*", "limit": 1000},
        headers={"x-org-id": _SEED_ORG_A},
    )
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    # Only org-A rows returned (filter auto-injected)
    assert all(r["org_id"] == _SEED_ORG_A for r in items)

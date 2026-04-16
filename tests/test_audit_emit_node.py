"""
Smoke tests for audit.events.emit — the canonical audit emitter.

Runs against the live tennetctl DB; each test cleans the test.* rows it
creates. Catalog is upserted once per test to register the audit feature
(already always_on, but upsert is idempotent + fast).
"""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import pytest

_catalog: Any = import_module("backend.01_catalog")
_ctx_mod: Any = import_module("backend.01_catalog.context")
_db: Any = import_module("backend.01_core.database")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

AUDIT_KEY = "audit.events.emit"


async def _setup(pool: Any) -> None:
    await _catalog.upsert_all(pool, frozenset({"core", "iam", "audit"}))


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "04_audit"."60_evt_audit" WHERE event_key LIKE $1',
            "test.%",
        )
    _catalog.clear_checkers()


async def _count_by_event_key(pool: Any, event_key: str) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            'SELECT count(*) FROM "04_audit"."60_evt_audit" WHERE event_key = $1',
            event_key,
        )


async def _fetch_audit_row(pool: Any, audit_id: str) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT * FROM "04_audit"."60_evt_audit" WHERE id = $1', audit_id,
        )
        return dict(row) if row else None


# ── AC-3: happy path + scope propagation ──────────────────────────


@pytest.mark.asyncio
async def test_audit_emit_writes_row_with_ctx_scope() -> None:
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup(pool)
        ctx = _ctx_mod.NodeContext(
            user_id="u1", session_id="s1",
            org_id="o1", workspace_id="w1",
            audit_category="user",
            trace_id="trace-1", span_id="span-caller",
        )
        result = await _catalog.run_node(
            pool, AUDIT_KEY, ctx,
            {"event_key": "test.happy", "outcome": "success", "metadata": {"k": "v"}},
        )
        assert "audit_id" in result
        row = await _fetch_audit_row(pool, result["audit_id"])
        assert row is not None
        assert row["actor_user_id"] == "u1"
        assert row["actor_session_id"] == "s1"
        assert row["org_id"] == "o1"
        assert row["workspace_id"] == "w1"
        assert row["trace_id"] == "trace-1"
        assert row["parent_span_id"] == "span-caller"
        assert row["event_key"] == "test.happy"
        assert row["audit_category"] == "user"
        assert row["outcome"] == "success"
        assert row["metadata"] == {"k": "v"} or row["metadata"] == '{"k": "v"}'
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


# ── AC-4: scope CHECK enforcement ─────────────────────────────────


@pytest.mark.asyncio
async def test_audit_emit_scope_rejected_when_partial_scope() -> None:
    """User category + authenticated user + partial scope (missing workspace_id) → CHECK rejects."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup(pool)
        # user_id set (authz passes) but workspace_id missing (CHECK rejects)
        ctx = _ctx_mod.NodeContext(
            audit_category="user",
            user_id="u1", session_id="s1", org_id="o1", workspace_id=None,
            trace_id="trace-2", span_id="span-2",
        )
        with pytest.raises(Exception) as excinfo:
            await _catalog.run_node(
                pool, AUDIT_KEY, ctx,
                {"event_key": "test.rejected", "outcome": "success"},
            )
        msg = str(excinfo.value)
        assert "chk_evt_audit_scope" in msg or "23514" in msg, f"unexpected error: {msg}"
        assert await _count_by_event_key(pool, "test.rejected") == 0
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_audit_emit_setup_category_bypasses_scope() -> None:
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup(pool)
        ctx = _ctx_mod.NodeContext(
            audit_category="setup",
            user_id=None, session_id=None, org_id=None, workspace_id=None,
            trace_id="trace-3", span_id="span-3",
        )
        result = await _catalog.run_node(
            pool, AUDIT_KEY, ctx,
            {"event_key": "test.setup_event", "outcome": "success"},
        )
        row = await _fetch_audit_row(pool, result["audit_id"])
        assert row is not None
        assert row["audit_category"] == "setup"
        assert row["actor_user_id"] is None
        assert row["org_id"] is None
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_audit_emit_failure_outcome_bypasses_scope() -> None:
    """System caller + failure outcome + no scope — authz passes (system), CHECK passes (failure bypass)."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup(pool)
        ctx = _ctx_mod.NodeContext(
            audit_category="system",
            user_id=None, session_id=None, org_id=None, workspace_id=None,
            trace_id="trace-4", span_id="span-4",
        )
        result = await _catalog.run_node(
            pool, AUDIT_KEY, ctx,
            {"event_key": "test.failure_event", "outcome": "failure"},
        )
        row = await _fetch_audit_row(pool, result["audit_id"])
        assert row is not None
        assert row["outcome"] == "failure"
        assert row["actor_user_id"] is None
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_audit_emit_system_success_requires_scope() -> None:
    """AC-4 edge: system category + success still requires full scope (only setup / failure bypass)."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup(pool)
        ctx = _ctx_mod.NodeContext.system()  # user_id None, audit_category='system'
        with pytest.raises(Exception) as excinfo:
            await _catalog.run_node(
                pool, AUDIT_KEY, ctx,
                {"event_key": "test.system_success_no_scope", "outcome": "success"},
            )
        msg = str(excinfo.value)
        assert "chk_evt_audit_scope" in msg or "23514" in msg
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)

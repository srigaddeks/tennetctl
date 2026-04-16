"""
Runner tests — covers NCP v1 §6 NodeContext, §7 run_node, §8 execution
policy, §9 authz hook.

Runs against the live tennetctl DB (same pattern as test_catalog_loader).
Each test sets up fixture rows and cleans them in a finally.
"""

from __future__ import annotations

import asyncio
import os
import time
from importlib import import_module
from typing import Any

import pytest

_catalog: Any = import_module("backend.01_catalog")
_db: Any = import_module("backend.01_core.database")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)


async def _setup_fixtures(pool: Any) -> None:
    """Upsert the fixture feature + reset stateful fixture counters."""
    # Reset stateful handlers (module-level state persists across tests).
    flaky_mod = import_module(
        "tests.fixtures.features.99_test_fixture.sub_features.01_sample.nodes.core_sample_flaky"
    )
    flaky_mod.FlakyNode._calls = 0

    broken_mod = import_module(
        "tests.fixtures.features.99_test_fixture.sub_features.01_sample.nodes.core_sample_broken"
    )
    broken_mod.BrokenNode._calls = 0

    await _catalog.upsert_all(pool, frozenset({"core"}), fixtures=True)


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "01_catalog"."12_fct_nodes" WHERE key LIKE $1',
            "core.%",
        )
        await conn.execute(
            'DELETE FROM "01_catalog"."11_fct_sub_features" WHERE key LIKE $1',
            "core.%",
        )
        await conn.execute(
            'DELETE FROM "01_catalog"."10_fct_features" WHERE key = $1',
            "core",
        )
    _catalog.clear_checkers()


# ── Tests ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_happy_echo() -> None:
    """AC-2: Happy path — run_node executes handler and returns validated output."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup_fixtures(pool)
        ctx = _catalog.NodeContext.system()
        out = await _catalog.run_node(pool, "core.sample.echo", ctx, {"msg": "hi"})
        assert out["msg"] == "hi"
        assert out["echoed"] is True
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_timeout_cancels_slow() -> None:
    """AC-3: timeout_ms=200 on slow node cancels the 2s sleep in <0.5s."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup_fixtures(pool)
        ctx = _catalog.NodeContext.system()
        start = time.perf_counter()
        with pytest.raises(_catalog.NodeTimeout):
            await _catalog.run_node(pool, "core.sample.slow", ctx, {})
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"timeout took {elapsed:.2f}s (expected <0.5s)"
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_retries_on_transient_error() -> None:
    """AC-4: flaky node fails twice then succeeds. Runner retries up to retries+1 attempts."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup_fixtures(pool)
        ctx = _catalog.NodeContext.system()
        out = await _catalog.run_node(
            pool,
            "core.sample.flaky",
            ctx,
            {"idempotency_key": "test-key-1"},
        )
        assert out["ok"] is True
        assert out["attempts"] == 3
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_idempotency_required_when_retries() -> None:
    """AC-4: nodes with retries>0 require idempotency_key. Handler never invoked if missing."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup_fixtures(pool)
        flaky_mod = import_module(
            "tests.fixtures.features.99_test_fixture.sub_features.01_sample.nodes.core_sample_flaky"
        )
        ctx = _catalog.NodeContext.system()
        with pytest.raises(_catalog.IdempotencyRequired):
            await _catalog.run_node(pool, "core.sample.flaky", ctx, {})
        assert flaky_mod.FlakyNode._calls == 0, "handler must not run when idempotency_key missing"
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_domain_error_no_retries() -> None:
    """AC-4: DomainError propagates without retry, even when node has retries=2."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup_fixtures(pool)
        broken_mod = import_module(
            "tests.fixtures.features.99_test_fixture.sub_features.01_sample.nodes.core_sample_broken"
        )
        ctx = _catalog.NodeContext.system()
        with pytest.raises(_catalog.DomainError):
            await _catalog.run_node(
                pool,
                "core.sample.broken",
                ctx,
                {"idempotency_key": "test-key-2"},
            )
        assert broken_mod.BrokenNode._calls == 1, "DomainError should NOT trigger retry"
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_auth_deny_without_user() -> None:
    """AC-5: user-category call without user_id raises NodeAuthDenied."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup_fixtures(pool)
        _context = import_module("backend.01_catalog.context")
        ctx = _context.NodeContext(
            audit_category="user",
            user_id=None,
            trace_id="t1",
            span_id="s1",
        )
        with pytest.raises(_catalog.NodeAuthDenied):
            await _catalog.run_node(pool, "core.sample.echo", ctx, {"msg": "hi"})
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_custom_checker_runs_first() -> None:
    """AC-5: custom checker denial runs before (and overrides) the default checker."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup_fixtures(pool)

        async def deny_core_sample(ctx: Any, node_meta: dict) -> None:
            if node_meta.get("key", "").startswith("core.sample."):
                raise _catalog.NodeAuthDenied(
                    "custom checker denies core.sample.*",
                    node_key=node_meta.get("key"),
                )

        _catalog.register_checker(deny_core_sample)

        # System ctx would otherwise pass the default checker.
        ctx = _catalog.NodeContext.system()
        with pytest.raises(_catalog.NodeAuthDenied) as excinfo:
            await _catalog.run_node(pool, "core.sample.echo", ctx, {"msg": "hi"})
        assert "custom checker" in str(excinfo.value)
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_unknown_key_raises() -> None:
    """AC-6: unknown key raises NodeNotFound."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup_fixtures(pool)
        ctx = _catalog.NodeContext.system()
        with pytest.raises(_catalog.NodeNotFound):
            await _catalog.run_node(pool, "core.sample.nope", ctx, {})
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_ctx_propagation() -> None:
    """AC-1: ctx propagates trace_id; span_id becomes parent_span_id in handler's ctx."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _setup_fixtures(pool)
        _context = import_module("backend.01_catalog.context")
        parent_ctx = _context.NodeContext(
            user_id="u1",
            session_id="s1",
            org_id="o1",
            workspace_id="w1",
            trace_id="trace-from-caller",
            span_id="span-caller",
            audit_category="system",
        )
        out = await _catalog.run_node(
            pool, "core.sample.echo", parent_ctx, {"msg": "ctx-test"},
        )
        assert out["trace_id"] == "trace-from-caller", "trace_id must propagate"
        assert out["parent_span_id"] == "span-caller", "caller span_id must become parent"
    finally:
        await _cleanup(pool)
        await _db.close_pool(pool)


if __name__ == "__main__":
    asyncio.run(test_happy_echo())
    print("manual run ok")

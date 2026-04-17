"""
Tests for auth_policy_bootstrap.ensure_policy_defaults.
Plan 20-01 AC-4.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_auth_policy_mod: Any = import_module("backend.02_features.03_iam.auth_policy")
_bootstrap: Any = import_module("backend.02_features.03_iam.auth_policy_bootstrap")
_configs_svc: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.service"
)
_configs_repo: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.repository"
)
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")


async def _cleanup_policy_rows(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "04_audit"."60_evt_audit" '
            "WHERE event_key LIKE 'vault.configs.%' "
            "  AND metadata->>'key' LIKE 'iam.policy.%'",
        )
        await conn.execute(
            """
            DELETE FROM "02_vault"."21_dtl_attrs"
            WHERE entity_id IN (
                SELECT id FROM "02_vault"."11_fct_vault_configs"
                WHERE key LIKE 'iam.policy.%'
            )
            """,
        )
        await conn.execute(
            "DELETE FROM \"02_vault\".\"11_fct_vault_configs\" WHERE key LIKE 'iam.policy.%'",
        )


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup_policy_rows(pool)
        try:
            yield pool
        finally:
            await _cleanup_policy_rows(pool)
            _catalog.clear_checkers()


@pytest.mark.asyncio
async def test_bootstrap_inserts_all_twenty_on_empty_table(live_app) -> None:
    pool = live_app
    inserted = await _bootstrap.ensure_policy_defaults(pool)
    assert inserted == 20

    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM \"02_vault\".\"11_fct_vault_configs\" "
            "WHERE key LIKE 'iam.policy.%' AND deleted_at IS NULL",
        )
    assert count == 20


@pytest.mark.asyncio
async def test_bootstrap_is_idempotent(live_app) -> None:
    pool = live_app
    first = await _bootstrap.ensure_policy_defaults(pool)
    assert first == 20

    second = await _bootstrap.ensure_policy_defaults(pool)
    assert second == 0

    async with pool.acquire() as conn:
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM \"02_vault\".\"11_fct_vault_configs\" "
            "WHERE key LIKE 'iam.policy.%' AND deleted_at IS NULL",
        )
    assert count == 20


@pytest.mark.asyncio
async def test_bootstrap_preserves_operator_overrides(live_app) -> None:
    pool = live_app
    from dataclasses import replace

    # Pre-insert password.min_length with a custom value (20 instead of default 12)
    ctx = _catalog_ctx.NodeContext(
        user_id="sys", session_id="test", org_id=None, workspace_id=None,
        trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(), audit_category="setup",
        extras={"pool": pool},
    )
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx_conn = replace(ctx, conn=conn)
            await _configs_svc.create_config(
                pool, conn, ctx_conn,
                key="iam.policy.password.min_length",
                value_type="number",
                value=20,
                description="operator tuned",
                scope="global",
                org_id=None,
                workspace_id=None,
            )

    # Bootstrap should skip that key and insert the remaining 19
    inserted = await _bootstrap.ensure_policy_defaults(pool)
    assert inserted == 19

    # The pre-inserted row must still have value 20, not 12
    async with pool.acquire() as conn:
        row = await _configs_repo.get_by_scope_key(
            conn, scope="global", org_id=None, workspace_id=None,
            key="iam.policy.password.min_length",
        )
    assert row is not None
    assert int(row["value"]) == 20

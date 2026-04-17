"""
Tests for AuthPolicy cache invalidation when vault.configs writes touch iam.policy.* keys.
Plan 20-01 AC-3.
"""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

import pytest

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")
_auth_policy_mod: Any = import_module("backend.02_features.03_iam.auth_policy")
_configs_svc: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.service"
)


def _make_ctx(pool: Any) -> Any:
    return _catalog_ctx.NodeContext(
        user_id="sys", session_id="test", org_id=None, workspace_id=None,
        trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(), audit_category="setup",
        extras={"pool": pool},
    )


async def _seed_policy(
    pool: Any,
    short_key: str,
    value: Any,
    value_type: str,
    scope: str = "global",
    org_id: str | None = None,
) -> str:
    ctx = _make_ctx(pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx_conn = replace(ctx, conn=conn)
            row = await _configs_svc.create_config(
                pool, conn, ctx_conn,
                key=f"iam.policy.{short_key}",
                value_type=value_type, value=value,
                description="inv-test", scope=scope, org_id=org_id, workspace_id=None,
            )
    return row["id"]


async def _update_config(pool: Any, config_id: str, value: Any) -> None:
    ctx = _make_ctx(pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx_conn = replace(ctx, conn=conn)
            await _configs_svc.update_config(
                pool, conn, ctx_conn,
                config_id=config_id, value=value, has_value=True,
            )


async def _delete_config(pool: Any, config_id: str) -> None:
    ctx = _make_ctx(pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx_conn = replace(ctx, conn=conn)
            await _configs_svc.delete_config(pool, conn, ctx_conn, config_id=config_id)


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
async def test_patch_org_override_invalidates_single_entry(live_app) -> None:
    pool = live_app
    org_a = _core_id.uuid7()
    org_b = _core_id.uuid7()

    await _seed_policy(pool, "lockout.duration_seconds", 300, "number", scope="global")
    cfg_id = await _seed_policy(pool, "lockout.duration_seconds", 600, "number",
                                scope="org", org_id=org_a)

    policy = _auth_policy_mod.AuthPolicy(pool, ttl_seconds=60.0)
    _configs_svc.set_auth_policy_ref(policy)

    assert await policy.resolve(org_a, "lockout.duration_seconds") == 600
    assert await policy.resolve(org_b, "lockout.duration_seconds") == 300
    hits_before = policy._fetch_count

    # Update per-org row → invalidates (org_a, "lockout.duration_seconds") only
    await _update_config(pool, cfg_id, 999)

    assert (org_a, "lockout.duration_seconds") not in policy._cache
    assert (org_b, "lockout.duration_seconds") in policy._cache  # org_b unaffected

    val_a = await policy.resolve(org_a, "lockout.duration_seconds")
    assert val_a == 999
    assert policy._fetch_count > hits_before

    # org_b resolve still hits cache (no additional DB hit)
    hits_after_a = policy._fetch_count
    await policy.resolve(org_b, "lockout.duration_seconds")
    assert policy._fetch_count == hits_after_a


@pytest.mark.asyncio
async def test_patch_global_invalidates_all_orgs_for_key(live_app) -> None:
    pool = live_app
    org_a = _core_id.uuid7()
    org_b = _core_id.uuid7()

    global_id = await _seed_policy(pool, "lockout.window_seconds", 300, "number", scope="global")
    # seed an unrelated key so we can verify it stays cached
    await _seed_policy(pool, "lockout.threshold_failed_attempts", 5, "number", scope="global")

    policy = _auth_policy_mod.AuthPolicy(pool, ttl_seconds=60.0)
    _configs_svc.set_auth_policy_ref(policy)

    assert await policy.resolve(org_a, "lockout.window_seconds") == 300
    assert await policy.resolve(org_b, "lockout.window_seconds") == 300
    assert await policy.resolve(None, "lockout.threshold_failed_attempts") == 5

    assert (org_a, "lockout.window_seconds") in policy._cache
    assert (org_b, "lockout.window_seconds") in policy._cache

    # Update global row → all cached entries for that key must be evicted
    await _update_config(pool, global_id, 888)

    assert (org_a, "lockout.window_seconds") not in policy._cache
    assert (org_b, "lockout.window_seconds") not in policy._cache
    # Unrelated key stays cached
    assert (None, "lockout.threshold_failed_attempts") in policy._cache

    assert await policy.resolve(org_a, "lockout.window_seconds") == 888
    assert await policy.resolve(org_b, "lockout.window_seconds") == 888


@pytest.mark.asyncio
async def test_delete_of_org_override_refolds_to_global(live_app) -> None:
    pool = live_app
    org_a = _core_id.uuid7()

    await _seed_policy(pool, "lockout.duration_seconds", 300, "number", scope="global")
    override_id = await _seed_policy(pool, "lockout.duration_seconds", 999, "number",
                                     scope="org", org_id=org_a)

    policy = _auth_policy_mod.AuthPolicy(pool, ttl_seconds=60.0)
    _configs_svc.set_auth_policy_ref(policy)

    assert await policy.resolve(org_a, "lockout.duration_seconds") == 999

    await _delete_config(pool, override_id)

    assert (org_a, "lockout.duration_seconds") not in policy._cache
    assert await policy.resolve(org_a, "lockout.duration_seconds") == 300

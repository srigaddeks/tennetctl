"""
Tests for AuthPolicy — resolver precedence, SWR cache, domain getters.
Plan 20-01 AC-1, AC-2, AC-5.
"""

from __future__ import annotations

import time
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
                value_type=value_type,
                value=value,
                description="test",
                scope=scope,
                org_id=org_id,
                workspace_id=None,
            )
    return row["id"]


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
async def test_resolve_global_only(live_app) -> None:
    pool = live_app
    await _seed_policy(pool, "password.min_length", 16, "number", scope="global")

    policy = _auth_policy_mod.AuthPolicy(pool)
    org_a = _core_id.uuid7()
    assert await policy.resolve(org_a, "password.min_length") == 16
    assert await policy.resolve(None, "password.min_length") == 16


@pytest.mark.asyncio
async def test_resolve_org_override_wins(live_app) -> None:
    pool = live_app
    org_a = _core_id.uuid7()
    org_b = _core_id.uuid7()

    await _seed_policy(pool, "lockout.duration_seconds", 300, "number", scope="global")
    await _seed_policy(pool, "lockout.duration_seconds", 600, "number", scope="org", org_id=org_a)

    policy = _auth_policy_mod.AuthPolicy(pool)
    assert await policy.resolve(org_a, "lockout.duration_seconds") == 600
    assert await policy.resolve(org_b, "lockout.duration_seconds") == 300
    assert await policy.resolve(None, "lockout.duration_seconds") == 300


@pytest.mark.asyncio
async def test_resolve_missing_returns_hardcoded_default(live_app) -> None:
    pool = live_app
    policy = _auth_policy_mod.AuthPolicy(pool)
    # No vault row seeded — must fall back to POLICY_KEYS default (12)
    val = await policy.resolve(None, "password.min_length")
    assert val == 12


@pytest.mark.asyncio
async def test_cache_hits_do_not_query_db(live_app) -> None:
    pool = live_app
    await _seed_policy(pool, "lockout.window_seconds", 300, "number", scope="global")

    policy = _auth_policy_mod.AuthPolicy(pool, ttl_seconds=60.0)
    assert policy._fetch_count == 0

    await policy.resolve(None, "lockout.window_seconds")
    assert policy._fetch_count == 1  # first call → DB hit

    await policy.resolve(None, "lockout.window_seconds")
    assert policy._fetch_count == 1  # second call within TTL → cache hit

    # Simulate TTL expiry
    policy._cache[(None, "lockout.window_seconds")] = (time.monotonic() - 61, 300)
    await policy.resolve(None, "lockout.window_seconds")
    assert policy._fetch_count == 2  # after expiry → DB hit again


@pytest.mark.asyncio
async def test_domain_getter_shape(live_app) -> None:
    pool = live_app
    await _seed_policy(pool, "password.min_length",       14,    "number",  scope="global")
    await _seed_policy(pool, "password.require_upper",    True,  "boolean", scope="global")
    await _seed_policy(pool, "password.require_digit",    True,  "boolean", scope="global")
    await _seed_policy(pool, "password.require_symbol",   False, "boolean", scope="global")
    await _seed_policy(pool, "password.min_unique_chars", 5,     "number",  scope="global")

    policy = _auth_policy_mod.AuthPolicy(pool)
    pw = await policy.password(None)

    assert isinstance(pw, _auth_policy_mod.PasswordPolicy)
    assert pw.min_length == 14
    assert pw.require_upper is True
    assert isinstance(pw.require_digit, bool)

    with pytest.raises(Exception):
        pw.min_length = 99  # type: ignore[misc]


@pytest.mark.asyncio
async def test_domain_getter_uses_org_override(live_app) -> None:
    pool = live_app
    org_a = _core_id.uuid7()

    await _seed_policy(pool, "password.min_length",       12,    "number",  scope="global")
    await _seed_policy(pool, "password.require_upper",    True,  "boolean", scope="global")
    await _seed_policy(pool, "password.require_digit",    True,  "boolean", scope="global")
    await _seed_policy(pool, "password.require_symbol",   False, "boolean", scope="global")
    await _seed_policy(pool, "password.min_unique_chars", 4,     "number",  scope="global")
    await _seed_policy(pool, "password.min_length",       20,    "number",  scope="org", org_id=org_a)

    policy = _auth_policy_mod.AuthPolicy(pool)
    assert (await policy.password(org_a)).min_length == 20
    assert (await policy.password(None)).min_length == 12

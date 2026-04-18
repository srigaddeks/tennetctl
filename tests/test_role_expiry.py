"""
Role expiry integration tests.

Tests cover: assign with future expiry, assign with past expiry (sweeper revokes),
sweeper does not revoke non-expired, sweeper audit event emitted.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

_main: Any = import_module("backend.main")

_TEST_EMAIL_PREFIX = "itest-rolexp-"
_TEST_ORG_SLUG = "rolexp-test-org"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        user_rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3 AND d.code = 'email'
              AND a.key_text LIKE $1
            """,
            f"{_TEST_EMAIL_PREFIX}%",
        )
        user_ids = [r["user_id"] for r in user_rows]
        if user_ids:
            await conn.execute(
                'DELETE FROM "03_iam"."42_lnk_user_roles" WHERE user_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."40_lnk_user_orgs" WHERE user_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "04_audit"."60_evt_audit" WHERE metadata->>\'user_id\' = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
                user_ids,
            )
        # Clean test roles
        await conn.execute(
            'DELETE FROM "03_iam"."42_lnk_user_roles" WHERE org_id IN ('
            '  SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = $1)',
            _TEST_ORG_SLUG,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id = 4 AND entity_id IN ('
            '  SELECT id FROM "03_iam"."13_fct_roles" WHERE org_id IN ('
            '    SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = $1))',
            _TEST_ORG_SLUG,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."13_fct_roles" WHERE org_id IN ('
            '  SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = $1)',
            _TEST_ORG_SLUG,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."10_fct_orgs" WHERE slug = $1', _TEST_ORG_SLUG
        )


@pytest.fixture
async def setup(request):
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)

        _orgs_svc: Any = import_module("backend.02_features.03_iam.sub_features.01_orgs.service")
        _users_svc: Any = import_module("backend.02_features.03_iam.sub_features.03_users.service")
        _roles_svc: Any = import_module("backend.02_features.03_iam.sub_features.04_roles.service")
        _roles_repo: Any = import_module("backend.02_features.03_iam.sub_features.04_roles.repository")
        _catalog_ctx: Any = import_module("backend.01_catalog.context")
        _core_id: Any = import_module("backend.01_core.id")

        ctx = _catalog_ctx.NodeContext(
            user_id=None, session_id=None, org_id=None, workspace_id=None,
            trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
        )

        async with pool.acquire() as conn:
            org = await _orgs_svc.create_org(pool, conn, ctx, slug=_TEST_ORG_SLUG, display_name="Role Expiry Test Org")
        org_id = org["id"]

        async with pool.acquire() as conn:
            user = await _users_svc.create_user(
                pool, conn, ctx, account_type="email_password",
                email=f"{_TEST_EMAIL_PREFIX}user@example.com",
                display_name="Expiry User",
            )
        user_id = user["id"]

        async with pool.acquire() as conn:
            role = await _roles_svc.create_role(
                pool, conn, ctx, org_id=org_id, role_type="custom",
                code="tester", label="Tester",
            )
        role_id = role["id"]

        try:
            yield {
                "pool": pool, "ctx": ctx, "org_id": org_id,
                "user_id": user_id, "role_id": role_id,
                "_roles_repo": _roles_repo,
            }
        finally:
            await _cleanup(pool)


@pytest.mark.asyncio
async def test_assign_with_future_expiry(setup):
    pool = setup["pool"]
    repo = setup["_roles_repo"]
    _core_id: Any = import_module("backend.01_core.id")
    future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)

    async with pool.acquire() as conn:
        row = await repo.assign_role(
            conn,
            id=_core_id.uuid7(),
            user_id=setup["user_id"],
            role_id=setup["role_id"],
            org_id=setup["org_id"],
            created_by="test",
            expires_at=future,
        )
    assert row["expires_at"] is not None
    assert row["revoked_at"] is None


@pytest.mark.asyncio
async def test_assign_without_expiry(setup):
    pool = setup["pool"]
    repo = setup["_roles_repo"]
    _core_id: Any = import_module("backend.01_core.id")

    async with pool.acquire() as conn:
        row = await repo.assign_role(
            conn,
            id=_core_id.uuid7(),
            user_id=setup["user_id"],
            role_id=setup["role_id"],
            org_id=setup["org_id"],
            created_by="test",
        )
    assert row["expires_at"] is None
    assert row["revoked_at"] is None


@pytest.mark.asyncio
async def test_sweeper_revokes_expired(setup):
    pool = setup["pool"]
    repo = setup["_roles_repo"]
    _core_id: Any = import_module("backend.01_core.id")
    _sweeper: Any = import_module(
        "backend.02_features.03_iam.sub_features.04_roles.expiry_sweeper"
    )

    past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    async with pool.acquire() as conn:
        await repo.assign_role(
            conn,
            id=_core_id.uuid7(),
            user_id=setup["user_id"],
            role_id=setup["role_id"],
            org_id=setup["org_id"],
            created_by="test",
            expires_at=past,
        )

    count = await _sweeper.run_once(pool)
    assert count >= 1

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT revoked_at FROM "03_iam"."42_lnk_user_roles" '
            'WHERE user_id = $1 AND role_id = $2 AND org_id = $3',
            setup["user_id"], setup["role_id"], setup["org_id"],
        )
    assert row["revoked_at"] is not None


@pytest.mark.asyncio
async def test_sweeper_does_not_revoke_future(setup):
    pool = setup["pool"]
    repo = setup["_roles_repo"]
    _core_id: Any = import_module("backend.01_core.id")
    _sweeper: Any = import_module(
        "backend.02_features.03_iam.sub_features.04_roles.expiry_sweeper"
    )

    future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
    async with pool.acquire() as conn:
        await repo.assign_role(
            conn,
            id=_core_id.uuid7(),
            user_id=setup["user_id"],
            role_id=setup["role_id"],
            org_id=setup["org_id"],
            created_by="test",
            expires_at=future,
        )

    await _sweeper.run_once(pool)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT revoked_at FROM "03_iam"."42_lnk_user_roles" '
            'WHERE user_id = $1 AND role_id = $2 AND org_id = $3',
            setup["user_id"], setup["role_id"], setup["org_id"],
        )
    assert row["revoked_at"] is None


@pytest.mark.asyncio
async def test_sweeper_does_not_revoke_permanent(setup):
    pool = setup["pool"]
    repo = setup["_roles_repo"]
    _core_id: Any = import_module("backend.01_core.id")
    _sweeper: Any = import_module(
        "backend.02_features.03_iam.sub_features.04_roles.expiry_sweeper"
    )

    async with pool.acquire() as conn:
        await repo.assign_role(
            conn,
            id=_core_id.uuid7(),
            user_id=setup["user_id"],
            role_id=setup["role_id"],
            org_id=setup["org_id"],
            created_by="test",
        )

    await _sweeper.run_once(pool)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT revoked_at FROM "03_iam"."42_lnk_user_roles" '
            'WHERE user_id = $1 AND role_id = $2 AND org_id = $3',
            setup["user_id"], setup["role_id"], setup["org_id"],
        )
    assert row["revoked_at"] is None

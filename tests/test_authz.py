"""
Integration tests for backend.01_core.authz.

Covers:
  1. User with role granting scope → require_permission passes.
  2. User without scope → raises FORBIDDEN.
  3. Expired role assignment → not counted (expires_at < now).
  4. Revoked role → not counted (revoked_at IS NOT NULL).
  5. Cross-org scope does not leak (role in org A, check scope in org B → fails).

Setup: uses the live DB via lifespan (same pattern as test_role_expiry.py).
Each test runs inside a shared fixture that creates a minimal set of IAM
rows (org, user, role, scope) and cleans up after itself.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import pytest

_main: Any = import_module("backend.main")

_TEST_SLUG = "authz-test-org"
_TEST_SLUG_B = "authz-test-org-b"
_TEST_EMAIL = "itest-authz@example.com"
_TEST_SCOPE_CODE = "authz:test:org"
_TEST_ROLE_CODE = "authz_test_role"

# dim_scopes rows we will insert manually — use a SMALLINT id that is very
# unlikely to collide with seeded data. Tests delete these rows on teardown.
_SCOPE_ID: int = 9001


async def _cleanup(pool: Any) -> None:
    """Remove all test artefacts in dependency order."""
    async with pool.acquire() as conn:
        # user-role links
        await conn.execute(
            """
            DELETE FROM "03_iam"."42_lnk_user_roles"
            WHERE org_id IN (
                SELECT id FROM "03_iam"."10_fct_orgs"
                WHERE slug = ANY($1::text[])
            )
            """,
            [_TEST_SLUG, _TEST_SLUG_B],
        )
        # role-scope links for our test scope
        await conn.execute(
            'DELETE FROM "03_iam"."44_lnk_role_scopes" WHERE scope_id = $1',
            _SCOPE_ID,
        )
        # dim_scopes test row
        await conn.execute(
            'DELETE FROM "03_iam"."03_dim_scopes" WHERE id = $1', _SCOPE_ID
        )
        # test roles (attrs + fct)
        for slug in (_TEST_SLUG, _TEST_SLUG_B):
            await conn.execute(
                """
                DELETE FROM "03_iam"."21_dtl_attrs"
                WHERE entity_type_id = 4
                  AND entity_id IN (
                    SELECT id FROM "03_iam"."13_fct_roles"
                    WHERE org_id IN (
                        SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = $1
                    )
                  )
                """,
                slug,
            )
            await conn.execute(
                """
                DELETE FROM "03_iam"."13_fct_roles"
                WHERE org_id IN (
                    SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = $1
                )
                """,
                slug,
            )
        # test users
        user_rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3 AND d.code = 'email'
              AND a.key_text = $1
            """,
            _TEST_EMAIL,
        )
        user_ids = [r["user_id"] for r in user_rows]
        if user_ids:
            await conn.execute(
                'DELETE FROM "03_iam"."40_lnk_user_orgs" WHERE user_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                """
                DELETE FROM "03_iam"."21_dtl_attrs"
                WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])
                """,
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
                user_ids,
            )
        # test orgs (attrs + fct)
        for slug in (_TEST_SLUG, _TEST_SLUG_B):
            await conn.execute(
                """
                DELETE FROM "03_iam"."21_dtl_attrs"
                WHERE entity_type_id = 1
                  AND entity_id IN (
                    SELECT id FROM "03_iam"."10_fct_orgs" WHERE slug = $1
                  )
                """,
                slug,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."10_fct_orgs" WHERE slug = $1', slug
            )


@pytest.fixture
async def authz_setup():
    """Fixture: lifespan + minimal IAM rows for authz tests.

    Yields a dict with keys: pool, user_id, org_id, org_b_id, role_id,
    scope_id, _core_id, _roles_repo.
    """
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)

        _orgs_svc: Any = import_module(
            "backend.02_features.03_iam.sub_features.01_orgs.service"
        )
        _users_svc: Any = import_module(
            "backend.02_features.03_iam.sub_features.03_users.service"
        )
        _roles_svc: Any = import_module(
            "backend.02_features.03_iam.sub_features.04_roles.service"
        )
        _roles_repo: Any = import_module(
            "backend.02_features.03_iam.sub_features.04_roles.repository"
        )
        _catalog_ctx: Any = import_module("backend.01_catalog.context")
        _core_id: Any = import_module("backend.01_core.id")

        ctx = _catalog_ctx.NodeContext(
            user_id=None, session_id=None, org_id=None, workspace_id=None,
            trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(), audit_category="setup",
            extras={"pool": pool},
        )

        # Create org A and org B
        async with pool.acquire() as conn:
            org = await _orgs_svc.create_org(
                pool, conn, ctx, slug=_TEST_SLUG, display_name="AuthZ Test Org A"
            )
        org_id = org["id"]

        async with pool.acquire() as conn:
            org_b = await _orgs_svc.create_org(
                pool, conn, ctx, slug=_TEST_SLUG_B, display_name="AuthZ Test Org B"
            )
        org_b_id = org_b["id"]

        # Create user
        async with pool.acquire() as conn:
            user = await _users_svc.create_user(
                pool, conn, ctx, account_type="email_password",
                email=_TEST_EMAIL, display_name="AuthZ Tester",
            )
        user_id = user["id"]

        # Create role in org A
        async with pool.acquire() as conn:
            role = await _roles_svc.create_role(
                pool, conn, ctx, org_id=org_id, role_type="custom",
                code=_TEST_ROLE_CODE, label="AuthZ Test Role",
            )
        role_id = role["id"]

        # Insert a test scope into dim_scopes (org-level scope for authz testing)
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO "03_iam"."03_dim_scopes"
                    (id, code, label, scope_level, description, deprecated_at)
                VALUES ($1, $2, $3, 'org', 'Test scope for authz unit tests', NULL)
                ON CONFLICT (id) DO NOTHING
                """,
                _SCOPE_ID, _TEST_SCOPE_CODE, "AuthZ Test Scope",
            )
            # Assign scope to the test role
            await conn.execute(
                """
                INSERT INTO "03_iam"."44_lnk_role_scopes"
                    (id, role_id, scope_id, created_by, created_at)
                VALUES ($1, $2, $3, 'test', CURRENT_TIMESTAMP)
                ON CONFLICT (role_id, scope_id) DO NOTHING
                """,
                _core_id.uuid7(), role_id, _SCOPE_ID,
            )

        try:
            yield {
                "pool": pool,
                "ctx": ctx,
                "org_id": org_id,
                "org_b_id": org_b_id,
                "user_id": user_id,
                "role_id": role_id,
                "_core_id": _core_id,
                "_roles_repo": _roles_repo,
            }
        finally:
            await _cleanup(pool)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_with_scope_passes(authz_setup):
    """User whose role grants the scope must not raise."""
    pool = authz_setup["pool"]
    repo = authz_setup["_roles_repo"]
    _core_id = authz_setup["_core_id"]
    _authz: Any = import_module("backend.01_core.authz")

    async with pool.acquire() as conn:
        await repo.assign_role(
            conn,
            id=_core_id.uuid7(),
            user_id=authz_setup["user_id"],
            role_id=authz_setup["role_id"],
            org_id=authz_setup["org_id"],
            created_by="test",
        )

    async with pool.acquire() as conn:
        # Must not raise
        await _authz.require_permission(
            conn,
            authz_setup["user_id"],
            _TEST_SCOPE_CODE,
            scope_org_id=authz_setup["org_id"],
        )


@pytest.mark.asyncio
async def test_user_without_scope_raises_forbidden(authz_setup):
    """User with no role assignment must receive FORBIDDEN."""
    pool = authz_setup["pool"]
    _authz: Any = import_module("backend.01_core.authz")
    _errors: Any = import_module("backend.01_core.errors")

    async with pool.acquire() as conn:
        with pytest.raises(_errors.AppError) as exc_info:
            await _authz.require_permission(
                conn,
                authz_setup["user_id"],
                _TEST_SCOPE_CODE,
                scope_org_id=authz_setup["org_id"],
            )
    assert exc_info.value.code == "FORBIDDEN"
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_expired_role_not_counted(authz_setup):
    """Role assignment with expires_at in the past must be ignored."""
    pool = authz_setup["pool"]
    repo = authz_setup["_roles_repo"]
    _core_id = authz_setup["_core_id"]
    _authz: Any = import_module("backend.01_core.authz")
    _errors: Any = import_module("backend.01_core.errors")

    past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)

    async with pool.acquire() as conn:
        await repo.assign_role(
            conn,
            id=_core_id.uuid7(),
            user_id=authz_setup["user_id"],
            role_id=authz_setup["role_id"],
            org_id=authz_setup["org_id"],
            created_by="test",
            expires_at=past,
        )

    async with pool.acquire() as conn:
        with pytest.raises(_errors.AppError) as exc_info:
            await _authz.require_permission(
                conn,
                authz_setup["user_id"],
                _TEST_SCOPE_CODE,
                scope_org_id=authz_setup["org_id"],
            )
    assert exc_info.value.code == "FORBIDDEN"


@pytest.mark.asyncio
async def test_revoked_role_not_counted(authz_setup):
    """Role assignment with revoked_at set must be ignored."""
    pool = authz_setup["pool"]
    _core_id = authz_setup["_core_id"]
    _authz: Any = import_module("backend.01_core.authz")
    _errors: Any = import_module("backend.01_core.errors")

    # Insert directly with revoked_at already set
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO "03_iam"."42_lnk_user_roles"
                (id, user_id, role_id, org_id, created_by, created_at,
                 expires_at, revoked_at)
            VALUES ($1, $2, $3, $4, 'test', CURRENT_TIMESTAMP, NULL,
                    CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, role_id, org_id) DO NOTHING
            """,
            _core_id.uuid7(),
            authz_setup["user_id"],
            authz_setup["role_id"],
            authz_setup["org_id"],
        )

    async with pool.acquire() as conn:
        with pytest.raises(_errors.AppError) as exc_info:
            await _authz.require_permission(
                conn,
                authz_setup["user_id"],
                _TEST_SCOPE_CODE,
                scope_org_id=authz_setup["org_id"],
            )
    assert exc_info.value.code == "FORBIDDEN"


@pytest.mark.asyncio
async def test_cross_org_scope_does_not_leak(authz_setup):
    """Role in org A must not grant scope when checking against org B."""
    pool = authz_setup["pool"]
    repo = authz_setup["_roles_repo"]
    _core_id = authz_setup["_core_id"]
    _authz: Any = import_module("backend.01_core.authz")
    _errors: Any = import_module("backend.01_core.errors")

    # Assign role in org A (valid, permanent)
    async with pool.acquire() as conn:
        await repo.assign_role(
            conn,
            id=_core_id.uuid7(),
            user_id=authz_setup["user_id"],
            role_id=authz_setup["role_id"],
            org_id=authz_setup["org_id"],
            created_by="test",
        )

    # Check scope against org B — must fail
    async with pool.acquire() as conn:
        with pytest.raises(_errors.AppError) as exc_info:
            await _authz.require_permission(
                conn,
                authz_setup["user_id"],
                _TEST_SCOPE_CODE,
                scope_org_id=authz_setup["org_b_id"],
            )
    assert exc_info.value.code == "FORBIDDEN"

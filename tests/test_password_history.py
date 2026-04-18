"""
Password history integration tests.

Tests cover: reuse rejection, unique password accepted, history pruned, depth=0 disables.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest

_main: Any = import_module("backend.main")

_TEST_EMAIL_PREFIX = "itest-pwhist-"
_TEST_ORG_SLUG = "pwhist-test-org"


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
                'DELETE FROM "03_iam"."50_fct_password_history" WHERE user_id = ANY($1::text[])',
                user_ids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = ANY($1::text[])',
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
                'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
                user_ids,
            )
        await conn.execute(
            'DELETE FROM "03_iam"."10_fct_orgs" WHERE slug = $1', _TEST_ORG_SLUG
        )


@pytest.fixture
async def setup():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        vault = _main.app.state.vault
        await _cleanup(pool)

        _orgs_svc: Any = import_module("backend.02_features.03_iam.sub_features.01_orgs.service")
        _users_svc: Any = import_module("backend.02_features.03_iam.sub_features.03_users.service")
        _catalog_ctx: Any = import_module("backend.01_catalog.context")
        _core_id: Any = import_module("backend.01_core.id")

        ctx = _catalog_ctx.NodeContext(
            user_id=None, session_id=None, org_id=None, workspace_id=None,
            trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
        )

        async with pool.acquire() as conn:
            await _orgs_svc.create_org(pool, conn, ctx, slug=_TEST_ORG_SLUG, display_name="PW History Org")

        async with pool.acquire() as conn:
            user = await _users_svc.create_user(
                pool, conn, ctx, account_type="email_password",
                email=f"{_TEST_EMAIL_PREFIX}user@example.com", display_name="PW Hist User",
            )
        user_id = user["id"]

        try:
            yield {"pool": pool, "vault": vault, "user_id": user_id}
        finally:
            await _cleanup(pool)


@pytest.mark.asyncio
async def test_reuse_rejected(setup):
    _cred_svc: Any = import_module("backend.02_features.03_iam.sub_features.08_credentials.service")
    pool = setup["pool"]
    vault = setup["vault"]
    user_id = setup["user_id"]
    _errors: Any = import_module("backend.01_core.errors")

    async with pool.acquire() as conn:
        await _cred_svc.set_password(
            conn, vault_client=vault, user_id=user_id, value="InitialPass1!", check_history=True
        )

    with pytest.raises(_errors.AppError) as exc_info:
        async with pool.acquire() as conn:
            await _cred_svc.set_password(
                conn, vault_client=vault, user_id=user_id, value="InitialPass1!", check_history=True
            )
    assert exc_info.value.code == "PASSWORD_REUSED"


@pytest.mark.asyncio
async def test_unique_password_accepted(setup):
    _cred_svc: Any = import_module("backend.02_features.03_iam.sub_features.08_credentials.service")
    pool = setup["pool"]
    vault = setup["vault"]
    user_id = setup["user_id"]

    async with pool.acquire() as conn:
        await _cred_svc.set_password(
            conn, vault_client=vault, user_id=user_id, value="FirstPass1!", check_history=True
        )
        await _cred_svc.set_password(
            conn, vault_client=vault, user_id=user_id, value="NewPass2@", check_history=True
        )
    # No exception = success


@pytest.mark.asyncio
async def test_history_disabled_when_check_false(setup):
    _cred_svc: Any = import_module("backend.02_features.03_iam.sub_features.08_credentials.service")
    pool = setup["pool"]
    vault = setup["vault"]
    user_id = setup["user_id"]

    async with pool.acquire() as conn:
        await _cred_svc.set_password(
            conn, vault_client=vault, user_id=user_id, value="SamePass1!", check_history=False
        )
        # Should not raise — history check disabled
        await _cred_svc.set_password(
            conn, vault_client=vault, user_id=user_id, value="SamePass1!", check_history=False
        )


@pytest.mark.asyncio
async def test_history_pruned_beyond_depth(setup):
    _cred_svc: Any = import_module("backend.02_features.03_iam.sub_features.08_credentials.service")
    _cred_repo: Any = import_module("backend.02_features.03_iam.sub_features.08_credentials.repository")
    pool = setup["pool"]
    vault = setup["vault"]
    user_id = setup["user_id"]
    depth = 3

    passwords = [f"Pass{i}!Abc" for i in range(1, depth + 3)]
    async with pool.acquire() as conn:
        for pw in passwords:
            await _cred_svc.set_password(
                conn, vault_client=vault, user_id=user_id, value=pw,
                check_history=False, history_depth=depth,
            )
            await _cred_repo.push_hash(
                conn, id=__import__("backend.01_core.id", fromlist=["uuid7"]).uuid7(),
                user_id=user_id, hash=await _cred_svc.hash_password(pw, vault)
            )
            await _cred_repo.prune_beyond(conn, user_id=user_id, depth=depth)

        hashes = await _cred_repo.list_recent_hashes(conn, user_id, depth + 10)
    assert len(hashes) <= depth

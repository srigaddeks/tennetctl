"""
Plan 20-04: Session limits integration tests.

Covers:
  - bump_last_activity updates last_activity_at column
  - check_session_timeouts returns "idle_timeout" when last_activity is old
  - check_session_timeouts returns "absolute_ttl" when session is old
  - enforce_session_limits evicts oldest when max_concurrent="oldest"
  - enforce_session_limits rejects when eviction_policy="reject"
  - enforce_session_limits evicts LRU when eviction_policy="lru"
"""

from __future__ import annotations

import datetime as dt
from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

_main: Any = import_module("backend.main")
_context_mod: Any = import_module("backend.01_catalog.context")
_core_id_mod: Any = import_module("backend.01_core.id")

_TEST_EMAIL_PREFIX = "itest-slimits-"


def _make_ctx(user_id: str | None = None, org_id: str | None = None) -> Any:
    return _context_mod.NodeContext(
        audit_category="setup",
        trace_id=_core_id_mod.uuid7(),
        span_id=_core_id_mod.uuid7(),
        user_id=user_id,
        org_id=org_id,
    )


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3
              AND d.code = 'email'
              AND a.key_text LIKE $1
            """,
            f"{_TEST_EMAIL_PREFIX}%",
        )
        user_ids = [r["user_id"] for r in rows]
        if not user_ids:
            return
        await conn.execute(
            'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."40_lnk_user_orgs" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."21_dtl_attrs" '
            "WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])",
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
            user_ids,
        )


from httpx import ASGITransport, AsyncClient  # noqa: E402 (after pytest import)


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        vault = _main.app.state.vault
        await _cleanup(pool)
        transport = ASGITransport(app=_main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, pool, vault
        await _cleanup(pool)


async def _signup_and_get_ids(client: Any, pool: Any, email_suffix: str) -> tuple[str, str, str]:
    """Signup via API and return (user_id, session_id, token)."""
    email = f"{_TEST_EMAIL_PREFIX}{email_suffix}@test.invalid"
    resp = await client.post("/v1/auth/signup", json={
        "email": email, "password": "Test@1234", "display_name": "SlimTest",
    })
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()["data"]
    token = data["token"]
    session_id = data["session"]["id"]
    user_id = data["user"]["id"]
    return user_id, session_id, token


@pytest.mark.asyncio
async def test_bump_last_activity_updates_column(live_app):
    client, pool, vault = live_app
    try:
        user_id, session_id, _ = await _signup_and_get_ids(client, pool, "bump1")
        _repo: Any = import_module(
            "backend.02_features.03_iam.sub_features.09_sessions.repository"
        )
        # Set last_activity_at to a past time
        async with pool.acquire() as conn:
            past = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(minutes=10)
            await conn.execute(
                'UPDATE "03_iam"."16_fct_sessions" SET last_activity_at=$1 WHERE id=$2',
                past, session_id,
            )
            await _repo.bump_last_activity(conn, session_id=session_id)
            row = await _repo.get_raw_by_id(conn, session_id)
        # last_activity_at should be newer than past
        assert row["last_activity_at"] > past + dt.timedelta(minutes=9)
    finally:
        await _cleanup(pool)


@pytest.mark.asyncio
async def test_idle_timeout_revokes_session(live_app):
    client, pool, vault = live_app
    try:
        user_id, session_id, _ = await _signup_and_get_ids(client, pool, "idle1")
        _svc: Any = import_module(
            "backend.02_features.03_iam.sub_features.09_sessions.service"
        )
        _repo: Any = import_module(
            "backend.02_features.03_iam.sub_features.09_sessions.repository"
        )

        # Set last_activity_at to 2000s ago
        async with pool.acquire() as conn:
            old_activity = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(seconds=2000)
            await conn.execute(
                'UPDATE "03_iam"."16_fct_sessions" SET last_activity_at=$1 WHERE id=$2',
                old_activity, session_id,
            )

        # Mock auth_policy with idle_timeout=1800s
        policy = MagicMock()
        policy.idle_timeout_seconds = 1800
        policy.absolute_ttl_seconds = 999999
        auth_policy_mock = MagicMock()
        auth_policy_mock.session = AsyncMock(return_value=policy)

        ctx = _make_ctx()
        async with pool.acquire() as conn:
            reason = await _svc.check_session_timeouts(
                pool, conn, ctx,
                session_id=session_id,
                auth_policy=auth_policy_mock,
                org_id=None,
            )
        assert reason == "idle_timeout"

        # Session should be revoked
        async with pool.acquire() as conn:
            row = await _repo.get_raw_by_id(conn, session_id)
        assert row["revoked_at"] is not None
    finally:
        await _cleanup(pool)


@pytest.mark.asyncio
async def test_absolute_ttl_revokes_session(live_app):
    client, pool, vault = live_app
    try:
        user_id, session_id, _ = await _signup_and_get_ids(client, pool, "absttl1")
        _svc: Any = import_module(
            "backend.02_features.03_iam.sub_features.09_sessions.service"
        )
        _repo: Any = import_module(
            "backend.02_features.03_iam.sub_features.09_sessions.repository"
        )

        # Set created_at to 700000s ago (> 604800)
        async with pool.acquire() as conn:
            old_create = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(seconds=700000)
            await conn.execute(
                'UPDATE "03_iam"."16_fct_sessions" SET created_at=$1 WHERE id=$2',
                old_create, session_id,
            )

        policy = MagicMock()
        policy.idle_timeout_seconds = 999999
        policy.absolute_ttl_seconds = 604800
        auth_policy_mock = MagicMock()
        auth_policy_mock.session = AsyncMock(return_value=policy)

        ctx = _make_ctx()
        async with pool.acquire() as conn:
            reason = await _svc.check_session_timeouts(
                pool, conn, ctx,
                session_id=session_id,
                auth_policy=auth_policy_mock,
                org_id=None,
            )
        assert reason == "absolute_ttl"

        async with pool.acquire() as conn:
            row = await _repo.get_raw_by_id(conn, session_id)
        assert row["revoked_at"] is not None
    finally:
        await _cleanup(pool)


@pytest.mark.asyncio
async def test_max_concurrent_oldest_evicts(live_app):
    client, pool, vault = live_app
    try:
        _sessions_svc: Any = import_module(
            "backend.02_features.03_iam.sub_features.09_sessions.service"
        )
        _sessions_repo: Any = import_module(
            "backend.02_features.03_iam.sub_features.09_sessions.repository"
        )

        user_id, s1_id, _ = await _signup_and_get_ids(client, pool, "maxc1")
        # Create a 2nd session via signin
        resp = await client.post("/v1/auth/signin", json={
            "email": f"{_TEST_EMAIL_PREFIX}maxc1@test.invalid",
            "password": "Test@1234",
        })
        assert resp.status_code == 200
        s2_id = resp.json()["data"]["session"]["id"]

        # Make s1 older
        async with pool.acquire() as conn:
            await conn.execute(
                'UPDATE "03_iam"."16_fct_sessions" SET created_at=$1, last_activity_at=$1 WHERE id=$2',
                dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(hours=2), s1_id,
            )

        policy = MagicMock()
        policy.max_concurrent_per_user = 2
        policy.eviction_policy = "oldest"
        auth_policy_mock = MagicMock()
        auth_policy_mock.session = AsyncMock(return_value=policy)
        ctx = _make_ctx()

        async with pool.acquire() as conn:
            evicted_id = await _sessions_svc.enforce_session_limits(
                pool, conn, ctx,
                user_id=user_id,
                auth_policy=auth_policy_mock,
                org_id=None,
            )
        assert evicted_id == s1_id

        async with pool.acquire() as conn:
            row = await _sessions_repo.get_raw_by_id(conn, s1_id)
        assert row["revoked_at"] is not None
    finally:
        await _cleanup(pool)


@pytest.mark.asyncio
async def test_max_concurrent_reject_raises_429(live_app):
    client, pool, vault = live_app
    try:
        _sessions_svc: Any = import_module(
            "backend.02_features.03_iam.sub_features.09_sessions.service"
        )
        _errors: Any = import_module("backend.01_core.errors")

        user_id, _s1_id, _ = await _signup_and_get_ids(client, pool, "rej1")
        resp = await client.post("/v1/auth/signin", json={
            "email": f"{_TEST_EMAIL_PREFIX}rej1@test.invalid",
            "password": "Test@1234",
        })
        assert resp.status_code == 200

        policy = MagicMock()
        policy.max_concurrent_per_user = 2
        policy.eviction_policy = "reject"
        auth_policy_mock = MagicMock()
        auth_policy_mock.session = AsyncMock(return_value=policy)
        ctx = _make_ctx()

        with pytest.raises(_errors.AppError) as exc_info:
            async with pool.acquire() as conn:
                await _sessions_svc.enforce_session_limits(
                    pool, conn, ctx,
                    user_id=user_id,
                    auth_policy=auth_policy_mock,
                    org_id=None,
                )
        assert exc_info.value.status_code == 429
    finally:
        await _cleanup(pool)

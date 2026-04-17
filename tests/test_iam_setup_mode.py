"""
Tests for first-run setup mode (plan 21-03).

Uses LIVE DB (DATABASE_URL) — assumes schemas are already migrated.
"""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_TEST_EMAIL = "setup-test-admin@tennetctl-e2e.dev"

_main: Any = import_module("backend.main")


async def _wipe_test_user(pool: Any) -> None:
    """Remove only the test user (by email) and the vault system.initialized config."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3 AND d.code = 'email'
              AND a.key_text = $1
            LIMIT 1
            """,
            _TEST_EMAIL,
        )
        if row:
            uid = row["user_id"]
            await conn.execute(
                'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = $1', uid
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_id = $1', uid
            )
            await conn.execute(
                'DELETE FROM "03_iam"."24_fct_iam_totp_credentials" WHERE user_id = $1', uid
            )
            await conn.execute(
                'DELETE FROM "03_iam"."28_fct_totp_backup_codes" WHERE user_id = $1', uid
            )
            await conn.execute(
                'DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = $1', uid
            )
            await conn.execute(
                'DELETE FROM "03_iam"."12_fct_users" WHERE id = $1', uid
            )
        await conn.execute(
            "DELETE FROM \"02_vault\".\"11_fct_vault_configs\" WHERE key = 'system.initialized'"
        )


@pytest.fixture
async def setup_pool():
    """Pool connected to live DB with test isolation."""
    pool = await asyncpg.create_pool(LIVE_DSN, min_size=1, max_size=3)
    await _wipe_test_user(pool)
    yield pool
    await _wipe_test_user(pool)
    await pool.close()


@pytest.fixture
async def setup_client():
    """HTTP client against the fully started app."""
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _wipe_test_user(pool)
        _main.app.state.setup_initialized = None
        transport = ASGITransport(app=_main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
        await _wipe_test_user(pool)


# ── Unit: repository ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_count_users_unit(setup_pool):
    _repo: Any = import_module(
        "backend.02_features.03_iam.sub_features.18_setup.repository"
    )
    async with setup_pool.acquire() as conn:
        count = await _repo.count_users(conn)
    assert isinstance(count, int)
    assert count >= 0


# ── API: setup status endpoint ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_setup_status_returns_correct_shape(setup_client):
    r = await setup_client.get("/v1/setup/status")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    data = body["data"]
    assert "initialized" in data
    assert "setup_required" in data
    assert "user_count" in data
    assert isinstance(data["user_count"], int)


@pytest.mark.asyncio
async def test_health_always_reachable(setup_client):
    r = await setup_client.get("/health")
    assert r.status_code == 200


# ── API: initial-admin already-initialized returns 409 ───────────────────────

@pytest.mark.asyncio
async def test_initial_admin_already_initialized_returns_409(setup_client):
    """When users already exist, POST /v1/setup/initial-admin returns 409."""
    # Check current state.
    status_r = await setup_client.get("/v1/setup/status")
    assert status_r.status_code == 200
    status = status_r.json()["data"]

    if not status["initialized"]:
        pytest.skip("DB has no users — skipping double-init test for live DB")

    payload = {
        "email": "another-admin@tennetctl-e2e.dev",
        "password": "SuperSecret123!",
        "display_name": "Another Admin",
    }
    r = await setup_client.post("/v1/setup/initial-admin", json=payload)
    assert r.status_code == 409
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ALREADY_INITIALIZED"


@pytest.mark.asyncio
async def test_setup_status_reflects_initialized_state(setup_client):
    """setup_required must be the inverse of initialized."""
    r = await setup_client.get("/v1/setup/status")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["setup_required"] == (not data["initialized"])


@pytest.mark.asyncio
async def test_initial_admin_endpoint_reachable(setup_client):
    """POST /v1/setup/initial-admin is always reachable (not blocked by setup middleware)."""
    r = await setup_client.post("/v1/setup/initial-admin", json={
        "email": "probe@tennetctl-e2e.dev",
        "password": "ShortPwd",
        "display_name": "",
    })
    # 409 (already initialized) or 422 (validation) are both OK — the route is reachable.
    assert r.status_code in (201, 409, 422), f"Unexpected: {r.status_code} {r.text}"

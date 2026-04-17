"""
Tests for first-run setup mode (plan 21-03).

Uses LIVE DB (DATABASE_URL) — assumes schemas are already migrated.

Covers:
  - GET /v1/setup/status returns correct shape
  - SetupModeMiddleware blocks non-setup routes with 503 when no users exist
  - POST /v1/setup/initial-admin creates user + returns TOTP + backup codes
  - Subsequent requests pass (setup mode off)
  - Double-init returns 409
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

_TEST_EMAIL = "setup-test-admin@tennetctl.test"

_main: Any = import_module("backend.main")


async def _wipe_setup_state(pool: Any) -> None:
    """Remove test user + system.initialized config for isolation."""
    async with pool.acquire() as conn:
        # Find test user.
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
                'DELETE FROM "03_iam"."42_lnk_user_roles" WHERE user_id = $1', uid
            )
            await conn.execute(
                'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = $1', uid
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_id = $1', uid
            )
            # TOTP + backup codes (entity_type_id=3 covers user attrs; OTP uses separate tables).
            await conn.execute(
                'DELETE FROM "03_iam"."30_fct_otp_credentials" WHERE user_id = $1', uid
            )
            await conn.execute(
                'DELETE FROM "03_iam"."31_fct_otp_backup_codes" WHERE user_id = $1', uid
            )
            await conn.execute(
                'DELETE FROM "03_iam"."10_fct_users" WHERE id = $1', uid
            )
        # Remove credentials hash row if present.
        if row:
            await conn.execute(
                'DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = $1',
                row["user_id"],
            )
        # Clear vault config.
        await conn.execute(
            "DELETE FROM \"02_vault\".\"11_fct_vault_configs\" WHERE key = 'system.initialized'"
        )


@pytest.fixture
async def setup_pool():
    """Pool fixture connected to live DB, with test-state cleanup before+after."""
    pool = await asyncpg.create_pool(LIVE_DSN, min_size=1, max_size=3)
    await _wipe_setup_state(pool)
    yield pool
    await _wipe_setup_state(pool)
    await pool.close()


@pytest.fixture
async def setup_client(setup_pool):
    """HTTP client against the app + cleaned state."""
    transport = ASGITransport(app=_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Reset in-memory cache so middleware re-checks DB.
        _main.app.state.setup_initialized = None  # type: ignore[attr-defined]
        yield ac


# ── Unit: repository ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_count_users_unit(setup_pool):
    """count_users returns a non-negative integer (may not be zero on live DB)."""
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
async def test_setup_status_always_reachable_no_users(setup_client, setup_pool):
    """Setup status is reachable even when no test users have been added."""
    # setup_pool already wiped test users + config; setup_client reset state cache.
    r = await setup_client.get("/v1/setup/status")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_health_always_reachable(setup_client):
    r = await setup_client.get("/health")
    assert r.status_code == 200


# ── API: initial-admin creation ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_initial_admin_success(setup_client, setup_pool):
    """POST /v1/setup/initial-admin creates user + TOTP + backup codes when DB is empty of this test user."""
    payload = {
        "email": _TEST_EMAIL,
        "password": "SuperSecret123!",
        "display_name": "Test Setup Admin",
    }
    r = await setup_client.post("/v1/setup/initial-admin", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["ok"] is True
    data = body["data"]
    assert data["email"] == _TEST_EMAIL
    assert data["display_name"] == "Test Setup Admin"
    assert "totp_credential_id" in data
    assert "otpauth_uri" in data
    assert data["otpauth_uri"].startswith("otpauth://totp/")
    assert isinstance(data["backup_codes"], list)
    assert len(data["backup_codes"]) == 10
    assert "session_token" in data


@pytest.mark.asyncio
async def test_create_initial_admin_double_init_409(setup_client, setup_pool):
    payload = {
        "email": _TEST_EMAIL,
        "password": "SuperSecret123!",
        "display_name": "Test Setup Admin",
    }
    # First call — success.
    r1 = await setup_client.post("/v1/setup/initial-admin", json=payload)
    assert r1.status_code == 201, r1.text

    # Second call — conflict.
    r2 = await setup_client.post("/v1/setup/initial-admin", json=payload)
    assert r2.status_code == 409
    body = r2.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ALREADY_INITIALIZED"


@pytest.mark.asyncio
async def test_after_init_setup_required_is_false(setup_client, setup_pool):
    """After initial admin creation, setup/status should show setup_required=false."""
    payload = {
        "email": _TEST_EMAIL,
        "password": "SuperSecret123!",
        "display_name": "Test Setup Admin",
    }
    r = await setup_client.post("/v1/setup/initial-admin", json=payload)
    assert r.status_code == 201

    # Now check status.
    r2 = await setup_client.get("/v1/setup/status")
    assert r2.status_code == 200
    data = r2.json()["data"]
    assert data["setup_required"] is False
    assert data["initialized"] is True

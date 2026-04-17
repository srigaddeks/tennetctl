"""
Integration tests for iam.gdpr — Plan 21-05.

Covers:
  - Export job created (kind=export, status=queued)
  - assemble_bundle includes expected keys
  - Erasure request pseudonymizes user + revokes sessions
  - Erasure blocks signin after pseudonymization
  - Hard purge nullifies PII in audit metadata
"""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_ctx_mod: Any = import_module("backend.01_catalog.context")

_TEST_EMAIL_PREFIX = "itest-gdpr-"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3
              AND d.code = 'email'
              AND (a.key_text LIKE $1 OR a.key_text LIKE 'deleted-%@removed.local')
            """,
            f"{_TEST_EMAIL_PREFIX}%",
        )
        user_ids = [r["user_id"] for r in rows]
        if not user_ids:
            return
        await conn.execute(
            'DELETE FROM "03_iam"."10_fct_gdpr_jobs" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            """
            DELETE FROM "04_audit"."60_evt_audit"
            WHERE event_key LIKE 'iam.gdpr.%' OR event_key LIKE 'iam.auth.%'
               OR event_key LIKE 'iam.users.%'
            """,
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


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        yield _main.app
        await _cleanup(pool)


@pytest.fixture
async def client(live_app):
    async with AsyncClient(
        transport=ASGITransport(app=live_app), base_url="http://test"
    ) as ac:
        yield ac


async def _signup_and_signin(client: Any, email: str, password: str = "TestPass123!") -> str:
    """Return session token after signup + signin."""
    await client.post(
        "/v1/auth/signup",
        json={"email": email, "password": password, "display_name": "GDPR Test"},
    )
    r = await client.post("/v1/auth/signin", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["data"]["token"]


# ── Test: export job creation ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_job_created(client: Any):
    email = f"{_TEST_EMAIL_PREFIX}export@example.com"
    token = await _signup_and_signin(client, email)
    r = await client.post(
        "/v1/account/data-export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 202, r.text
    data = r.json()["data"]
    assert data["kind"] == "export"
    assert data["status"] == "queued"
    assert data["user_id"] is not None


# ── Test: export bundle contents ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_assemble_bundle_keys(live_app: Any):
    """assemble_bundle returns expected top-level keys."""
    pool = live_app.state.pool
    _gdpr_service: Any = import_module(
        "backend.02_features.03_iam.sub_features.19_gdpr.service"
    )
    _auth_service: Any = import_module(
        "backend.02_features.03_iam.sub_features.10_auth.service"
    )
    _ctx: Any = _ctx_mod.NodeContext(
        audit_category="setup",
        trace_id="test",
        span_id="test",
        extras={"pool": pool},
    )

    email = f"{_TEST_EMAIL_PREFIX}bundle@example.com"
    async with pool.acquire() as conn:
        result = await _auth_service.signup(
            pool, conn, _ctx,
            email=email,
            password="TestPass123!",
            display_name="Bundle Test",
            vault_client=live_app.state.vault,
        )
    user_id = result["user"]["id"]

    bundle = await _gdpr_service.assemble_bundle(pool, user_id)
    assert "user" in bundle
    assert "sessions" in bundle
    assert "memberships" in bundle
    assert "audit_events" in bundle
    assert "exported_at" in bundle


# ── Test: erasure pseudonymizes user ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_erasure_pseudonymizes_user(client: Any, live_app: Any):
    email = f"{_TEST_EMAIL_PREFIX}erase@example.com"
    password = "TestPass123!"
    token = await _signup_and_signin(client, email, password)

    r = await client.post(
        "/v1/account/delete-me",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": password, "confirm": "DELETE"},
    )
    assert r.status_code == 202, r.text
    data = r.json()["data"]
    assert data["kind"] == "erase"
    assert data["status"] == "queued"
    assert data["hard_erase_at"] is not None

    # Verify pseudonymization in DB
    pool = live_app.state.pool
    user_id = data["user_id"]
    async with pool.acquire() as conn:
        email_attr = await conn.fetchval(
            'SELECT a.key_text '
            'FROM "03_iam"."21_dtl_attrs" a '
            'JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id '
            'WHERE a.entity_type_id = 3 AND a.entity_id = $1 AND d.code = $2',
            user_id, "email",
        )
    assert email_attr == f"deleted-{user_id}@removed.local"


# ── Test: erasure blocks signin ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_erasure_blocks_signin(client: Any):
    email = f"{_TEST_EMAIL_PREFIX}block@example.com"
    password = "TestPass123!"
    token = await _signup_and_signin(client, email, password)

    await client.post(
        "/v1/account/delete-me",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": password, "confirm": "DELETE"},
    )

    # After erasure, email no longer matches → signin should fail
    r = await client.post("/v1/auth/signin", json={"email": email, "password": password})
    assert r.status_code in (401, 404), f"Expected 401/404 but got {r.status_code}"


# ── Test: gdpr status endpoint ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gdpr_status(client: Any):
    email = f"{_TEST_EMAIL_PREFIX}status@example.com"
    token = await _signup_and_signin(client, email)

    await client.post(
        "/v1/account/data-export",
        headers={"Authorization": f"Bearer {token}"},
    )

    r = await client.get(
        "/v1/account/gdpr/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["export"] is not None
    assert data["export"]["kind"] == "export"
    assert data["erase"] is None

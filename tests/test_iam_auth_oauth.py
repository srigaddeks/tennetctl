"""
OAuth integration tests — Google + GitHub.

The provider HTTP round-trip is monkeypatched via the service's _exchange_google
/ _exchange_github stubs, so the tests exercise everything downstream: vault
key lookup, user upsert, email-collision check, default-org attach (single
tenant), session mint, audit emission.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_auth_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.10_auth.service"
)

_TEST_EMAIL_PREFIX = "itest-oauth-"


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
            """
            DELETE FROM "04_audit"."60_evt_audit"
            WHERE metadata->>'user_id' = ANY($1::text[])
            """,
            user_ids,
        )
        await conn.execute(
            """
            DELETE FROM "03_iam"."40_lnk_user_orgs"
            WHERE user_id = ANY($1::text[])
            """,
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


@pytest.fixture
async def live_app(monkeypatch):
    async def fake_google(code: str, redirect_uri: str, vault_client: Any) -> dict:
        # Emulate a successful round-trip. Email carries the test prefix so the
        # post-test cleanup reclaims the row.
        if code == "boom":
            from importlib import import_module as _im
            _errors = _im("backend.01_core.errors")
            raise _errors.UnauthorizedError("google token exchange failed (status=400)")
        return {
            "email": f"{_TEST_EMAIL_PREFIX}{code}@example.com",
            "display_name": f"Google {code}",
            "avatar_url": "https://example.com/a.png",
        }

    async def fake_github(code: str, redirect_uri: str, vault_client: Any) -> dict:
        return {
            "email": f"{_TEST_EMAIL_PREFIX}{code}@example.com",
            "display_name": f"GH {code}",
            "avatar_url": None,
        }

    monkeypatch.setattr(_auth_service, "_exchange_google", fake_google)
    monkeypatch.setattr(_auth_service, "_exchange_github", fake_github)

    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac, pool
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


@pytest.mark.asyncio
async def test_oauth_google_happy_path(live_app) -> None:
    client, pool = live_app
    r = await client.post(
        "/v1/auth/google",
        json={"code": "alice", "redirect_uri": "http://test/cb"},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["token"]
    assert data["user"]["account_type"] == "google_oauth"
    assert data["user"]["email"] == f"{_TEST_EMAIL_PREFIX}alice@example.com"
    assert data["user"]["avatar_url"] == "https://example.com/a.png"
    assert data["session"]["is_valid"] is True

    # Second call with same code is idempotent (reuses the same user).
    r2 = await client.post(
        "/v1/auth/google",
        json={"code": "alice", "redirect_uri": "http://test/cb"},
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["user"]["id"] == data["user"]["id"]

    # Audit event fires for each oauth_google call.
    async with pool.acquire() as conn:
        n = await conn.fetchval(
            """
            SELECT count(*) FROM "04_audit"."60_evt_audit"
            WHERE event_key = 'iam.auth.oauth.google'
              AND metadata->>'user_id' = $1
            """,
            data["user"]["id"],
        )
    assert n == 2


@pytest.mark.asyncio
async def test_oauth_github_happy_path(live_app) -> None:
    client, _pool = live_app
    r = await client.post(
        "/v1/auth/github",
        json={"code": "bob", "redirect_uri": "http://test/cb"},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["user"]["account_type"] == "github_oauth"
    assert data["user"]["email"] == f"{_TEST_EMAIL_PREFIX}bob@example.com"


@pytest.mark.asyncio
async def test_oauth_exchange_failure_returns_401(live_app) -> None:
    client, _pool = live_app
    r = await client.post(
        "/v1/auth/google",
        json={"code": "boom", "redirect_uri": "http://test/cb"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_oauth_collides_with_email_password(live_app) -> None:
    client, _pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}collide@example.com"

    # First: register as email_password.
    sp = await client.post(
        "/v1/auth/signup",
        json={"email": email, "display_name": "Collide", "password": "password password"},
    )
    assert sp.status_code == 201

    # Then: try to sign in via Google with the same email — should 409.
    r = await client.post(
        "/v1/auth/google",
        json={"code": "collide", "redirect_uri": "http://test/cb"},
    )
    assert r.status_code == 409, r.text
    assert r.json()["error"]["code"] == "CONFLICT"
    assert "email_password" in r.json()["error"]["message"]


@pytest.mark.asyncio
async def test_signup_single_tenant_attaches_default_org(live_app) -> None:
    """Signup in single-tenant mode must place the user in the default org."""
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}st@example.com"

    sp = await client.post(
        "/v1/auth/signup",
        json={"email": email, "display_name": "Solo", "password": "password password"},
    )
    assert sp.status_code == 201
    user_id = sp.json()["data"]["user"]["id"]
    org_id = sp.json()["data"]["session"]["org_id"]
    assert org_id is not None, "single-tenant signup must attach to default org"

    async with pool.acquire() as conn:
        slug = await conn.fetchval(
            'SELECT slug FROM "03_iam"."v_orgs" WHERE id = $1', org_id,
        )
        assert slug == "default"
        member_count = await conn.fetchval(
            'SELECT count(*) FROM "03_iam"."40_lnk_user_orgs" '
            "WHERE user_id = $1 AND org_id = $2",
            user_id, org_id,
        )
    assert member_count == 1


@pytest.mark.asyncio
async def test_oauth_state_concept_is_frontend(live_app) -> None:
    """
    The state parameter is enforced client-side (oauth-callback.tsx compares URL
    state vs sessionStorage). This test documents that the backend does NOT
    receive or check state — only {code, redirect_uri}. Changing this requires
    revisiting the frontend contract.
    """
    client, _pool = live_app
    r = await client.post(
        "/v1/auth/google",
        json={"code": "no-state", "redirect_uri": "http://test/cb"},
    )
    assert r.status_code == 200

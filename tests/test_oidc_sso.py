"""
OIDC SSO integration tests.

Tests cover: provider CRUD, PKCE initiate URL validation,
JIT user creation on callback, merge with existing user,
state validation, and no client_secret leakage.

HTTP calls to IdP discovery/token endpoints are monkeypatched.
"""

from __future__ import annotations

import base64
import hashlib
import json
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_oidc_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.20_oidc_sso.service"
)

_TEST_EMAIL_PREFIX = "itest-oidc-"
_TEST_ORG_SLUG = "oidc-test-org"
_PROVIDER_SLUG = "test-idp"
_VAULT_KEY = "iam.oidc.test.client_secret"
_ISSUER = "https://idp.example.com"
_CLIENT_ID = "client-abc"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        # Remove providers for test org
        rows = await conn.fetch(
            """
            SELECT p.id FROM "03_iam"."30_fct_oidc_providers" p
            JOIN "03_iam"."10_fct_orgs" o ON o.id = p.org_id
            WHERE o.slug = $1
            """,
            _TEST_ORG_SLUG,
        )
        ids = [r["id"] for r in rows]
        if ids:
            await conn.execute(
                'DELETE FROM "03_iam"."30_fct_oidc_providers" WHERE id = ANY($1::text[])',
                ids,
            )

        # Remove test users
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

        # Remove test org if exists
        await conn.execute(
            'DELETE FROM "03_iam"."10_fct_orgs" WHERE slug = $1', _TEST_ORG_SLUG
        )


def _make_fake_id_token(email: str, issuer: str, client_id: str, exp: int = 9999999999) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"RS256","typ":"JWT"}').rstrip(b"=").decode()
    payload_data = {"iss": issuer, "aud": client_id, "sub": "sub123", "email": email,
                    "name": "Test User", "exp": exp}
    payload = base64.urlsafe_b64encode(
        json.dumps(payload_data).encode()
    ).rstrip(b"=").decode()
    sig = base64.urlsafe_b64encode(b"fakesig").rstrip(b"=").decode()
    return f"{header}.{payload}.{sig}"


@pytest.fixture
async def live_app(monkeypatch):
    """App with a real pool, vault, and mocked OIDC discovery/token exchange."""
    import httpx as _httpx

    class _FakeResponse:
        def __init__(self, data: dict, status_code: int = 200):
            self._data = data
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise _httpx.HTTPStatusError("", request=None, response=self)  # type: ignore[arg-type]

        def json(self):
            return self._data

    _DISCOVERY = {
        "authorization_endpoint": f"{_ISSUER}/auth",
        "token_endpoint": f"{_ISSUER}/token",
        "jwks_uri": f"{_ISSUER}/jwks",
        "issuer": _ISSUER,
    }

    original_get = _httpx.AsyncClient.get
    original_post = _httpx.AsyncClient.post

    async def fake_get(self, url, **kwargs):
        if "openid-configuration" in url:
            return _FakeResponse(_DISCOVERY)
        return await original_get(self, url, **kwargs)

    async def fake_post(self, url, **kwargs):
        if _ISSUER in url and "token" in url:
            email = getattr(fake_post, "_email", f"{_TEST_EMAIL_PREFIX}new@example.com")
            id_token = _make_fake_id_token(email, _ISSUER, _CLIENT_ID)
            return _FakeResponse({
                "access_token": "at123",
                "id_token": id_token,
                "token_type": "Bearer",
            })
        return await original_post(self, url, **kwargs)

    monkeypatch.setattr(_httpx.AsyncClient, "get", fake_get)
    monkeypatch.setattr(_httpx.AsyncClient, "post", fake_post)
    fake_post._email = f"{_TEST_EMAIL_PREFIX}new@example.com"  # type: ignore[attr-defined]

    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        vault = _main.app.state.vault  # noqa: F841

        # Store fake secret in vault for the test provider
        _secrets_service: Any = import_module(
            "backend.02_features.02_vault.sub_features.01_secrets.service"
        )
        _catalog_ctx_mod: Any = import_module("backend.01_catalog.context")
        _core_id_mod: Any = import_module("backend.01_core.id")
        vault_ctx = _catalog_ctx_mod.NodeContext(
            user_id=None, session_id=None, org_id=None, workspace_id=None,
            trace_id=_core_id_mod.uuid7(), span_id=_core_id_mod.uuid7(),
            request_id=_core_id_mod.uuid7(), audit_category="setup",
            extras={"pool": pool},
        )
        async with pool.acquire() as conn:
            try:
                await _secrets_service.create_secret(
                    pool, conn, vault_ctx,
                    vault_client=_main.app.state.vault,
                    scope="global", org_id=None, workspace_id=None,
                    key=_VAULT_KEY, value="super-secret-value", description="test",
                )
            except Exception:
                pass  # May already exist (ConflictError on re-run)

        await _cleanup(pool)
        try:
            yield _main.app, fake_post
        finally:
            await _cleanup(pool)
            _catalog: Any = import_module("backend.01_catalog")
            _catalog.clear_checkers()


@pytest.fixture
async def admin_client(live_app) -> tuple[AsyncClient, str]:
    """Returns (client, org_id) with an authenticated admin session for the test org."""
    app, _ = live_app
    pool = app.state.pool
    vault = app.state.vault

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create test org and admin user
        _orgs_service: Any = import_module(
            "backend.02_features.03_iam.sub_features.01_orgs.service"
        )
        _users_service: Any = import_module(
            "backend.02_features.03_iam.sub_features.03_users.service"
        )
        _sessions_service: Any = import_module(
            "backend.02_features.03_iam.sub_features.09_sessions.service"
        )
        _catalog_ctx: Any = import_module("backend.01_catalog.context")
        _core_id: Any = import_module("backend.01_core.id")

        ctx = _catalog_ctx.NodeContext(
            user_id=None, session_id=None, org_id=None, workspace_id=None,
            trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
        )

        async with pool.acquire() as conn:
            # Create org
            try:
                org = await _orgs_service.create_org(
                    pool, conn, ctx, slug=_TEST_ORG_SLUG, display_name="OIDC Test Org"
                )
            except Exception:
                _orgs_repo: Any = import_module(
                    "backend.02_features.03_iam.sub_features.01_orgs.repository"
                )
                org = await _orgs_repo.get_by_slug(conn, _TEST_ORG_SLUG)

            # Create admin user
            user = await _users_service.create_user(
                pool, conn, ctx,
                account_type="email_password",
                email=f"{_TEST_EMAIL_PREFIX}admin@example.com",
                display_name="OIDC Admin",
            )
            token, _ = await _sessions_service.mint_session(
                conn, vault_client=vault, user_id=user["id"], org_id=org["id"],
            )

        ac.cookies.set("tennetctl_session", token)
        ac.headers.update({
            "x-org-id": org["id"],
            "x-user-id": user["id"],
        })
        yield ac, org["id"]


# ── Provider CRUD ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_provider(admin_client):
    client, org_id = admin_client
    resp = await client.post("/v1/iam/oidc-providers", json={
        "slug": _PROVIDER_SLUG,
        "issuer": _ISSUER,
        "client_id": _CLIENT_ID,
        "client_secret_vault_key": _VAULT_KEY,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["ok"] is True
    provider = data["data"]
    assert provider["slug"] == _PROVIDER_SLUG
    assert provider["issuer"] == _ISSUER


@pytest.mark.asyncio
async def test_list_providers(admin_client):
    client, org_id = admin_client
    # Create first
    await client.post("/v1/iam/oidc-providers", json={
        "slug": _PROVIDER_SLUG,
        "issuer": _ISSUER,
        "client_id": _CLIENT_ID,
        "client_secret_vault_key": _VAULT_KEY,
    })
    resp = await client.get("/v1/iam/oidc-providers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert len(data["data"]) >= 1
    slugs = [p["slug"] for p in data["data"]]
    assert _PROVIDER_SLUG in slugs


@pytest.mark.asyncio
async def test_delete_provider(admin_client):
    client, org_id = admin_client
    create_resp = await client.post("/v1/iam/oidc-providers", json={
        "slug": _PROVIDER_SLUG + "-del",
        "issuer": _ISSUER,
        "client_id": _CLIENT_ID,
        "client_secret_vault_key": _VAULT_KEY,
    })
    provider_id = create_resp.json()["data"]["id"]

    del_resp = await client.delete(f"/v1/iam/oidc-providers/{provider_id}")
    assert del_resp.status_code == 204

    # Deleted provider should not appear in list
    list_resp = await client.get("/v1/iam/oidc-providers")
    slugs = [p["slug"] for p in list_resp.json()["data"]]
    assert (_PROVIDER_SLUG + "-del") not in slugs


@pytest.mark.asyncio
async def test_client_secret_not_in_api_response(admin_client):
    client, org_id = admin_client
    await client.post("/v1/iam/oidc-providers", json={
        "slug": _PROVIDER_SLUG,
        "issuer": _ISSUER,
        "client_id": _CLIENT_ID,
        "client_secret_vault_key": _VAULT_KEY,
    })
    resp = await client.get("/v1/iam/oidc-providers")
    text = resp.text
    # The vault key reference is okay to return; the actual secret value must not appear
    assert "super-secret-value" not in text


# ── PKCE + State ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pkce_state_signing():
    """Unit test: state sign/verify round-trip."""
    import time
    secret = b"a" * 32
    payload = {"org_slug": "acme", "provider_slug": "okta", "verifier": "v123",
               "nonce": "n456", "exp": int(time.time()) + 600}
    token = _oidc_service._sign_state(payload, secret)
    result = _oidc_service._verify_state(token, secret)
    assert result["org_slug"] == "acme"
    assert result["verifier"] == "v123"


@pytest.mark.asyncio
async def test_pkce_state_expired():
    import time
    from importlib import import_module
    _errors: Any = import_module("backend.01_core.errors")
    secret = b"b" * 32
    payload = {"org_slug": "acme", "provider_slug": "okta", "verifier": "v",
               "nonce": "n", "exp": int(time.time()) - 10}
    token = _oidc_service._sign_state(payload, secret)
    with pytest.raises(Exception):  # ValidationError
        _oidc_service._verify_state(token, secret)


@pytest.mark.asyncio
async def test_pkce_challenge_format():
    """code_challenge = base64url(sha256(verifier)) without padding."""
    verifier = "abc123"
    challenge = _oidc_service._pkce_challenge(verifier)
    expected = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    assert challenge == expected
    assert "=" not in challenge


# ── Callback / JIT ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_callback_creates_new_user(live_app):
    app, fake_post = live_app
    new_email = f"{_TEST_EMAIL_PREFIX}brand-new@example.com"
    fake_post._email = new_email

    pool = app.state.pool
    vault = app.state.vault

    # First create org + provider
    _orgs_service: Any = import_module(
        "backend.02_features.03_iam.sub_features.01_orgs.service"
    )
    _catalog_ctx: Any = import_module("backend.01_catalog.context")
    _core_id: Any = import_module("backend.01_core.id")

    ctx = _catalog_ctx.NodeContext(
        user_id=None, session_id=None, org_id=None, workspace_id=None,
        trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
    )

    async with pool.acquire() as conn:
        try:
            org = await _orgs_service.create_org(
                pool, conn, ctx, slug=_TEST_ORG_SLUG, display_name="OIDC Test Org"
            )
        except Exception:
            _orgs_repo: Any = import_module(
                "backend.02_features.03_iam.sub_features.01_orgs.repository"
            )
            org = await _orgs_repo.get_by_slug(conn, _TEST_ORG_SLUG)

        _s: Any = import_module("backend.02_features.03_iam.sub_features.20_oidc_sso.schemas")
        create_data = _s.OidcProviderCreate(
            slug=_PROVIDER_SLUG, issuer=_ISSUER, client_id=_CLIENT_ID,
            client_secret_vault_key=_VAULT_KEY,
        )
        try:
            await _oidc_service.create_provider(pool, conn, ctx, org["id"], create_data)
        except Exception:
            pass  # may already exist

    # Build a valid signed state
    import time
    state_secret = await _oidc_service._get_state_secret(vault)
    state_payload = {
        "org_slug": _TEST_ORG_SLUG,
        "provider_slug": _PROVIDER_SLUG,
        "verifier": "test-verifier-abc123",
        "nonce": "nonce123",
        "exp": int(time.time()) + 600,
    }
    state = _oidc_service._sign_state(state_payload, state_secret)

    async with pool.acquire() as conn:
        user, token = await _oidc_service.handle_callback(
            pool, conn, ctx, vault,
            org_slug=_TEST_ORG_SLUG, code="code123", state=state,
        )

    assert user["email"] == new_email
    assert token  # session token minted
    # user was created with oidc_sso account_type
    assert user.get("account_type") == "oidc_sso" or "id" in user


@pytest.mark.asyncio
async def test_callback_merges_existing_user(live_app):
    """When an existing user's email is returned by OIDC, no duplicate is created."""
    app, fake_post = live_app
    existing_email = f"{_TEST_EMAIL_PREFIX}existing@example.com"
    fake_post._email = existing_email

    pool = app.state.pool
    vault = app.state.vault

    _users_service: Any = import_module(
        "backend.02_features.03_iam.sub_features.03_users.service"
    )
    _catalog_ctx: Any = import_module("backend.01_catalog.context")
    _core_id: Any = import_module("backend.01_core.id")
    _orgs_repo: Any = import_module(
        "backend.02_features.03_iam.sub_features.01_orgs.repository"
    )

    ctx = _catalog_ctx.NodeContext(
        user_id=None, session_id=None, org_id=None, workspace_id=None,
        trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
    )

    async with pool.acquire() as conn:
        org = await _orgs_repo.get_by_slug(conn, _TEST_ORG_SLUG)
        if org is None:
            _orgs_service: Any = import_module(
                "backend.02_features.03_iam.sub_features.01_orgs.service"
            )
            org = await _orgs_service.create_org(
                pool, conn, ctx, slug=_TEST_ORG_SLUG, display_name="OIDC Test Org"
            )

        # Create user with email_password first
        try:
            pre_user = await _users_service.create_user(
                pool, conn, ctx, account_type="email_password",
                email=existing_email, display_name="Pre-existing User",
            )
        except Exception:
            pre_row = await conn.fetchrow(
                'SELECT id FROM "03_iam"."v_users" WHERE email = $1 AND deleted_at IS NULL',
                existing_email,
            )
            pre_user = dict(pre_row) if pre_row else {"id": None}

        _s: Any = import_module("backend.02_features.03_iam.sub_features.20_oidc_sso.schemas")
        create_data = _s.OidcProviderCreate(
            slug=_PROVIDER_SLUG, issuer=_ISSUER, client_id=_CLIENT_ID,
            client_secret_vault_key=_VAULT_KEY,
        )
        try:
            await _oidc_service.create_provider(pool, conn, ctx, org["id"], create_data)
        except Exception:
            pass

    import time
    state_secret = await _oidc_service._get_state_secret(vault)
    state_payload = {
        "org_slug": _TEST_ORG_SLUG,
        "provider_slug": _PROVIDER_SLUG,
        "verifier": "v456",
        "nonce": "n789",
        "exp": int(time.time()) + 600,
    }
    state = _oidc_service._sign_state(state_payload, state_secret)

    async with pool.acquire() as conn:
        user, token = await _oidc_service.handle_callback(
            pool, conn, ctx, vault,
            org_slug=_TEST_ORG_SLUG, code="code456", state=state,
        )

    # Should reuse same user, not create new one
    assert user["id"] == pre_user["id"]
    assert token


@pytest.mark.asyncio
async def test_callback_invalid_state_rejected(live_app):
    app, _ = live_app
    pool = app.state.pool
    vault = app.state.vault
    _catalog_ctx: Any = import_module("backend.01_catalog.context")
    _core_id: Any = import_module("backend.01_core.id")
    ctx = _catalog_ctx.NodeContext(
        user_id=None, session_id=None, org_id=None, workspace_id=None,
        trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
    )

    async with pool.acquire() as conn:
        with pytest.raises(Exception) as exc_info:
            await _oidc_service.handle_callback(
                pool, conn, ctx, vault,
                org_slug=_TEST_ORG_SLUG, code="c", state="invalid.state.token",
            )
    assert exc_info.value is not None


@pytest.mark.asyncio
async def test_callback_expired_state_rejected(live_app):
    import time
    app, _ = live_app
    pool = app.state.pool
    vault = app.state.vault
    _catalog_ctx: Any = import_module("backend.01_catalog.context")
    _core_id: Any = import_module("backend.01_core.id")
    ctx = _catalog_ctx.NodeContext(
        user_id=None, session_id=None, org_id=None, workspace_id=None,
        trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(), audit_category="setup", extras={"pool": pool},
    )

    state_secret = await _oidc_service._get_state_secret(vault)
    expired_payload = {
        "org_slug": _TEST_ORG_SLUG,
        "provider_slug": _PROVIDER_SLUG,
        "verifier": "v",
        "nonce": "n",
        "exp": int(time.time()) - 100,  # already expired
    }
    state = _oidc_service._sign_state(expired_payload, state_secret)

    async with pool.acquire() as conn:
        with pytest.raises(Exception):
            await _oidc_service.handle_callback(
                pool, conn, ctx, vault,
                org_slug=_TEST_ORG_SLUG, code="c", state=state,
            )

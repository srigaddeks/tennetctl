"""
SAML 2.0 SSO integration tests.

Tests cover: provider CRUD, SP metadata, SP-initiated redirect,
ACS JIT user creation, ACS JIT merge with existing user,
invalid SAMLResponse rejection, expired relay_state rejection.

OneLogin_Saml2_Auth is monkeypatched — no real IdP required.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from importlib import import_module
from typing import Any
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_saml_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.21_saml_sso.service"
)

_TEST_EMAIL_PREFIX = "itest-saml-"
_TEST_ORG_SLUG = "saml-test-org"
_IDP_ENTITY_ID = "https://idp.example.com/saml2/metadata"
_SSO_URL = "https://idp.example.com/saml2/sso"
_SP_ENTITY_ID = "https://sp.example.com"
_X509_CERT = "MIICxDCCAaygAwIBAgIITesting="  # fake cert

_PROVIDER_BODY = {
    "idp_entity_id": _IDP_ENTITY_ID,
    "sso_url": _SSO_URL,
    "x509_cert": _X509_CERT,
    "sp_entity_id": _SP_ENTITY_ID,
}


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _sign_relay_state(payload: dict, secret: bytes) -> str:
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64url_encode(hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{sig}"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT p.id FROM "03_iam"."31_fct_saml_providers" p
            JOIN "03_iam"."10_fct_orgs" o ON o.id = p.org_id
            WHERE o.slug = $1
            """,
            _TEST_ORG_SLUG,
        )
        ids = [r["id"] for r in rows]
        if ids:
            await conn.execute(
                'DELETE FROM "03_iam"."31_fct_saml_providers" WHERE id = ANY($1::text[])',
                ids,
            )

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

        await conn.execute(
            'DELETE FROM "03_iam"."10_fct_orgs" WHERE slug = $1', _TEST_ORG_SLUG
        )


def _make_mock_saml_auth(*, email: str | None = None, errors: list | None = None,
                          authenticated: bool = True, last_error: str | None = None) -> MagicMock:
    mock = MagicMock()
    mock.process_response = MagicMock()
    mock.get_errors.return_value = errors or []
    mock.is_authenticated.return_value = authenticated
    mock.get_nameid.return_value = email
    mock.get_attributes.return_value = {}
    mock.get_last_error_reason.return_value = last_error
    mock.login.return_value = f"{_SSO_URL}?SAMLRequest=abc123"
    return mock


@pytest.fixture
async def live_app(monkeypatch):
    """App with real pool/vault and mocked OneLogin_Saml2_Auth."""
    _auth_module: Any = import_module(
        "backend.02_features.03_iam.sub_features.21_saml_sso.service"
    )

    _mock_email = [f"{_TEST_EMAIL_PREFIX}new@example.com"]
    _mock_errors: list = []
    _mock_authenticated = [True]
    _mock_last_error: list[str | None] = [None]

    class _MockSamlAuth:
        def __init__(self, req: Any, settings: Any) -> None:
            pass

        def process_response(self) -> None:
            pass

        def get_errors(self) -> list:
            return _mock_errors

        def is_authenticated(self) -> bool:
            return _mock_authenticated[0]

        def get_nameid(self) -> str | None:
            return _mock_email[0]

        def get_attributes(self) -> dict:
            return {}

        def get_last_error_reason(self) -> str | None:
            return _mock_last_error[0]

        def login(self, return_to: str = "") -> str:
            return f"{_SSO_URL}?SAMLRequest=abc123&RelayState={return_to}"

    class _MockSamlSettings:
        def __init__(self, settings: Any, sp_validation_only: bool = False) -> None:
            pass

        def get_sp_metadata(self) -> str:
            return '<?xml version="1.0"?><EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata" entityID="test"/>'

    import sys
    onelogin_mock = MagicMock()
    onelogin_mock.saml2 = MagicMock()
    onelogin_mock.saml2.auth = MagicMock()
    onelogin_mock.saml2.auth.OneLogin_Saml2_Auth = _MockSamlAuth
    onelogin_mock.saml2.settings = MagicMock()
    onelogin_mock.saml2.settings.OneLogin_Saml2_Settings = _MockSamlSettings
    sys.modules["onelogin"] = onelogin_mock
    sys.modules["onelogin.saml2"] = onelogin_mock.saml2
    sys.modules["onelogin.saml2.auth"] = onelogin_mock.saml2.auth
    sys.modules["onelogin.saml2.settings"] = onelogin_mock.saml2.settings

    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        vault = _main.app.state.vault

        await _cleanup(pool)

        _orgs_service: Any = import_module(
            "backend.02_features.03_iam.sub_features.01_orgs.service"
        )
        _catalog_ctx_mod: Any = import_module("backend.01_catalog.context")
        _core_id_mod: Any = import_module("backend.01_core.id")
        ctx = _catalog_ctx_mod.NodeContext(
            user_id=None, session_id=None, org_id=None, workspace_id=None,
            trace_id=_core_id_mod.uuid7(), span_id=_core_id_mod.uuid7(),
            request_id=_core_id_mod.uuid7(), audit_category="setup",
            extras={"pool": pool},
        )
        async with pool.acquire() as conn:
            org = await _orgs_service.create_org(pool, conn, ctx, slug=_TEST_ORG_SLUG, display_name="SAML Test Org")
        org_id = org["id"]

        try:
            yield {
                "app": _main.app,
                "pool": pool,
                "vault": vault,
                "org_id": org_id,
                "mock_email": _mock_email,
                "mock_errors": _mock_errors,
                "mock_authenticated": _mock_authenticated,
                "mock_last_error": _mock_last_error,
            }
        finally:
            await _cleanup(pool)


@pytest.fixture
async def authed_client(live_app):
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        cookies={"tennetctl_session": "bad"},
    ) as client:
        pool = live_app["pool"]
        org_id = live_app["org_id"]

        _users_service: Any = import_module(
            "backend.02_features.03_iam.sub_features.03_users.service"
        )
        _sessions_service: Any = import_module(
            "backend.02_features.03_iam.sub_features.09_sessions.service"
        )
        _catalog_ctx_mod: Any = import_module("backend.01_catalog.context")
        _core_id_mod: Any = import_module("backend.01_core.id")
        vault = live_app["vault"]

        ctx = _catalog_ctx_mod.NodeContext(
            user_id=None, session_id=None, org_id=org_id, workspace_id=None,
            trace_id=_core_id_mod.uuid7(), span_id=_core_id_mod.uuid7(),
            request_id=_core_id_mod.uuid7(), audit_category="setup",
            extras={"pool": pool},
        )
        async with pool.acquire() as conn:
            admin = await _users_service.create_user(
                pool, conn, ctx, account_type="email_password",
                email=f"{_TEST_EMAIL_PREFIX}admin@example.com",
                display_name="SAML Admin",
            )
            token, _ = await _sessions_service.mint_session(
                conn, vault_client=vault, user_id=admin["id"], org_id=org_id,
            )

        client.cookies.set("tennetctl_session", token)
        yield client


# ── CRUD tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_provider(authed_client):
    resp = await authed_client.post("/v1/iam/saml-providers", json=_PROVIDER_BODY)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["idp_entity_id"] == _IDP_ENTITY_ID
    assert data["sso_url"] == _SSO_URL
    assert data["enabled"] is True


@pytest.mark.asyncio
async def test_list_providers(authed_client):
    await authed_client.post("/v1/iam/saml-providers", json=_PROVIDER_BODY)
    resp = await authed_client.get("/v1/iam/saml-providers")
    assert resp.status_code == 200
    body = resp.json()
    providers = body["data"] if isinstance(body["data"], list) else [body["data"]]
    assert len(providers) >= 1


@pytest.mark.asyncio
async def test_delete_provider(authed_client):
    create_resp = await authed_client.post("/v1/iam/saml-providers", json=_PROVIDER_BODY)
    provider_id = create_resp.json()["data"]["id"]
    del_resp = await authed_client.delete(f"/v1/iam/saml-providers/{provider_id}")
    assert del_resp.status_code == 204
    list_resp = await authed_client.get("/v1/iam/saml-providers")
    ids = [p["id"] for p in list_resp.json()["data"]]
    assert provider_id not in ids


@pytest.mark.asyncio
async def test_x509_cert_stripped_of_pem_headers(authed_client):
    body = {**_PROVIDER_BODY, "x509_cert": f"-----BEGIN CERTIFICATE-----\n{_X509_CERT}\n-----END CERTIFICATE-----"}
    resp = await authed_client.post("/v1/iam/saml-providers", json=body)
    assert resp.status_code == 201
    stored_cert = resp.json()["data"]["x509_cert"]
    assert "-----BEGIN" not in stored_cert


# ── SP metadata ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sp_metadata_xml(live_app, authed_client):
    await authed_client.post("/v1/iam/saml-providers", json=_PROVIDER_BODY)
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
    ) as anon_client:
        resp = await anon_client.get(f"/v1/auth/saml/{_TEST_ORG_SLUG}/metadata")
    assert resp.status_code == 200
    assert "xml" in resp.headers["content-type"]
    assert "EntityDescriptor" in resp.text


# ── SP-initiated flow ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_initiate_redirect(live_app, authed_client):
    await authed_client.post("/v1/iam/saml-providers", json=_PROVIDER_BODY)
    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        follow_redirects=False,
    ) as anon_client:
        resp = await anon_client.get(f"/v1/auth/saml/{_TEST_ORG_SLUG}/initiate")
    assert resp.status_code == 302
    assert _SSO_URL in resp.headers["location"]


# ── ACS / JIT upsert ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_acs_jit_creates_new_user(live_app, authed_client):
    await authed_client.post("/v1/iam/saml-providers", json=_PROVIDER_BODY)
    new_email = f"{_TEST_EMAIL_PREFIX}jit-new@example.com"
    live_app["mock_email"][0] = new_email

    state_secret = hashlib.sha256("iam.saml.state_secret".encode()).digest()
    relay_state = _sign_relay_state(
        {"org_slug": _TEST_ORG_SLUG, "nonce": "abc", "exp": int(time.time()) + 600},
        state_secret,
    )

    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        follow_redirects=False,
    ) as anon_client:
        resp = await anon_client.post(
            f"/v1/auth/saml/{_TEST_ORG_SLUG}/acs",
            data={"SAMLResponse": "fakeresponse", "RelayState": relay_state},
        )
    assert resp.status_code == 303
    assert "tennetctl_session" in resp.cookies

    pool = live_app["pool"]
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            """
            SELECT a.entity_id FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3 AND d.code = 'email' AND a.key_text = $1
            """,
            new_email,
        )
    assert user is not None


@pytest.mark.asyncio
async def test_acs_jit_merges_existing_user(live_app, authed_client):
    await authed_client.post("/v1/iam/saml-providers", json=_PROVIDER_BODY)
    existing_email = f"{_TEST_EMAIL_PREFIX}existing@example.com"
    live_app["mock_email"][0] = existing_email

    pool = live_app["pool"]
    _users_service: Any = import_module(
        "backend.02_features.03_iam.sub_features.03_users.service"
    )
    _catalog_ctx_mod: Any = import_module("backend.01_catalog.context")
    _core_id_mod: Any = import_module("backend.01_core.id")
    ctx = _catalog_ctx_mod.NodeContext(
        user_id=None, session_id=None, org_id=live_app["org_id"], workspace_id=None,
        trace_id=_core_id_mod.uuid7(), span_id=_core_id_mod.uuid7(),
        request_id=_core_id_mod.uuid7(), audit_category="setup", extras={"pool": pool},
    )
    async with pool.acquire() as conn:
        existing_user = await _users_service.create_user(
            pool, conn, ctx, account_type="email_password",
            email=existing_email, display_name="Pre-existing",
        )

    state_secret = hashlib.sha256("iam.saml.state_secret".encode()).digest()
    relay_state = _sign_relay_state(
        {"org_slug": _TEST_ORG_SLUG, "nonce": "xyz", "exp": int(time.time()) + 600},
        state_secret,
    )

    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        follow_redirects=False,
    ) as anon_client:
        resp = await anon_client.post(
            f"/v1/auth/saml/{_TEST_ORG_SLUG}/acs",
            data={"SAMLResponse": "fakeresponse", "RelayState": relay_state},
        )
    assert resp.status_code == 303

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT a.entity_id FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3 AND d.code = 'email' AND a.key_text = $1
            """,
            existing_email,
        )
    assert len(rows) == 1
    assert rows[0]["entity_id"] == existing_user["id"]


@pytest.mark.asyncio
async def test_acs_invalid_saml_response_rejected(live_app, authed_client):
    await authed_client.post("/v1/iam/saml-providers", json=_PROVIDER_BODY)
    live_app["mock_authenticated"][0] = False
    live_app["mock_errors"].append("saml_validation_failed")
    live_app["mock_last_error"][0] = "Invalid assertion"

    state_secret = hashlib.sha256("iam.saml.state_secret".encode()).digest()
    relay_state = _sign_relay_state(
        {"org_slug": _TEST_ORG_SLUG, "nonce": "bad", "exp": int(time.time()) + 600},
        state_secret,
    )

    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        follow_redirects=False,
    ) as anon_client:
        resp = await anon_client.post(
            f"/v1/auth/saml/{_TEST_ORG_SLUG}/acs",
            data={"SAMLResponse": "bad", "RelayState": relay_state},
        )
    assert resp.status_code == 302
    assert "saml_failed" in resp.headers["location"]


@pytest.mark.asyncio
async def test_acs_expired_relay_state_rejected(live_app, authed_client):
    await authed_client.post("/v1/iam/saml-providers", json=_PROVIDER_BODY)

    state_secret = hashlib.sha256("iam.saml.state_secret".encode()).digest()
    expired_relay = _sign_relay_state(
        {"org_slug": _TEST_ORG_SLUG, "nonce": "exp", "exp": int(time.time()) - 1},
        state_secret,
    )

    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        follow_redirects=False,
    ) as anon_client:
        resp = await anon_client.post(
            f"/v1/auth/saml/{_TEST_ORG_SLUG}/acs",
            data={"SAMLResponse": "fakeresponse", "RelayState": expired_relay},
        )
    assert resp.status_code == 302
    assert "saml_failed" in resp.headers["location"]


@pytest.mark.asyncio
async def test_acs_tampered_relay_state_rejected(live_app, authed_client):
    await authed_client.post("/v1/iam/saml-providers", json=_PROVIDER_BODY)

    async with AsyncClient(
        transport=ASGITransport(app=live_app["app"]),
        base_url="http://test",
        follow_redirects=False,
    ) as anon_client:
        resp = await anon_client.post(
            f"/v1/auth/saml/{_TEST_ORG_SLUG}/acs",
            data={"SAMLResponse": "fakeresponse", "RelayState": "tampered.fakesig"},
        )
    assert resp.status_code == 302
    assert "saml_failed" in resp.headers["location"]

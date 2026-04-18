"""
iam.saml_sso — service layer.

SP-initiated SAML 2.0 flow:
  initiate: build signed AuthnRequest → 302 to IdP SSO URL
  acs: validate SAMLResponse → JIT upsert user → mint session

State/relay_state: HMAC-signed payload (org_slug + timestamp), TTL 10 min.
x509_cert stored in DB (public IdP cert — not a secret).
JIT upsert: match existing user by email across any account_type.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.21_saml_sso.repository"
)
_users_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_sessions_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)

_STATE_SECRET_VAULT_KEY = "iam.saml.state_secret"
_STATE_TTL_SECONDS = 600
_ACCOUNT_TYPE_SAML_SSO = "saml_sso"
_AUDIT_NODE_KEY = "audit.events.emit"


async def _emit_audit(pool: Any, ctx: Any, *, event_key: str, metadata: dict, outcome: str = "success") -> None:
    try:
        await _catalog.run_node(pool, _AUDIT_NODE_KEY, ctx, {"event_key": event_key, "outcome": outcome, "metadata": metadata})
    except Exception:
        pass


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


async def _get_state_secret(vault_client: Any) -> bytes:
    try:
        raw = await vault_client.get(_STATE_SECRET_VAULT_KEY)
        return base64.b64decode(raw)
    except Exception:
        return hashlib.sha256(_STATE_SECRET_VAULT_KEY.encode()).digest()


def _sign_relay_state(payload: dict, secret: bytes) -> str:
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64url_encode(hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{sig}"


def _verify_relay_state(token: str, secret: bytes) -> dict:
    try:
        body_part, sig_part = token.rsplit(".", 1)
    except ValueError as exc:
        raise _errors.ValidationError("invalid relay_state format") from exc
    expected = _b64url_encode(hmac.new(secret, body_part.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, sig_part):
        raise _errors.ValidationError("relay_state signature invalid")
    payload = json.loads(_b64url_decode(body_part))
    if payload.get("exp", 0) < time.time():
        raise _errors.ValidationError("relay_state expired")
    return payload


def _build_saml_settings(provider: dict, acs_url: str) -> dict:
    cert = provider["x509_cert"]
    if not cert.startswith("-----"):
        cert = f"-----BEGIN CERTIFICATE-----\n{cert}\n-----END CERTIFICATE-----"
    return {
        "strict": True,
        "debug": False,
        "sp": {
            "entityId": provider["sp_entity_id"],
            "assertionConsumerService": {
                "url": acs_url,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
            "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        },
        "idp": {
            "entityId": provider["idp_entity_id"],
            "singleSignOnService": {
                "url": provider["sso_url"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": provider["x509_cert"],
        },
    }


# ── SP Metadata ───────────────────────────────────────────────────────────────

async def get_sp_metadata_xml(conn: Any, org_slug: str, acs_url: str) -> str:
    from onelogin.saml2.settings import OneLogin_Saml2_Settings  # type: ignore[import-untyped]

    provider = await _repo.get_by_org_slug(conn, org_slug)
    if provider is None:
        raise _errors.NotFoundError(f"No enabled SAML provider for org {org_slug!r}")

    settings = OneLogin_Saml2_Settings(_build_saml_settings(provider, acs_url), sp_validation_only=True)
    metadata = settings.get_sp_metadata()
    return metadata


# ── Provider CRUD ─────────────────────────────────────────────────────────────

async def list_providers(conn: Any, org_id: str) -> list[dict]:
    return await _repo.get_by_org(conn, org_id)


async def create_provider(pool: Any, conn: Any, ctx: Any, org_id: str, data: Any) -> dict:
    provider_id = _core_id.uuid7()
    row = await _repo.create(conn, org_id=org_id, id=provider_id, data=data)
    await _emit_audit(pool, ctx, event_key="iam.saml.provider.created",
                      metadata={"provider_id": provider_id, "org_id": org_id})
    return row


async def delete_provider(pool: Any, conn: Any, ctx: Any, provider_id: str, org_id: str) -> None:
    existing = await _repo.get_by_id(conn, provider_id, org_id)
    if existing is None:
        raise _errors.NotFoundError(f"SAML provider {provider_id!r} not found")
    await _repo.soft_delete(conn, provider_id=provider_id, org_id=org_id)
    await _emit_audit(pool, ctx, event_key="iam.saml.provider.deleted",
                      metadata={"provider_id": provider_id, "org_id": org_id})


# ── SP-initiated AuthnRequest ─────────────────────────────────────────────────

async def build_initiate_redirect(
    conn: Any, vault_client: Any, *, org_slug: str, base_url: str,
) -> str:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth  # type: ignore[import-untyped]

    provider = await _repo.get_by_org_slug(conn, org_slug)
    if provider is None:
        raise _errors.NotFoundError(f"No enabled SAML provider for org {org_slug!r}")

    acs_url = f"{base_url}/v1/auth/saml/{org_slug}/acs"
    settings = _build_saml_settings(provider, acs_url)

    state_secret = await _get_state_secret(vault_client)
    relay_state = _sign_relay_state(
        {"org_slug": org_slug, "nonce": secrets.token_hex(16), "exp": int(time.time()) + _STATE_TTL_SECONDS},
        state_secret,
    )

    req = {
        "https": "on",
        "http_host": base_url.replace("https://", "").replace("http://", ""),
        "script_name": f"/v1/auth/saml/{org_slug}/initiate",
        "get_data": {},
        "post_data": {},
    }
    auth = OneLogin_Saml2_Auth(req, settings)
    redirect_url = auth.login(return_to=relay_state)
    return redirect_url


# ── ACS / JIT upsert ─────────────────────────────────────────────────────────

async def handle_acs(
    pool: Any, conn: Any, ctx: Any, vault_client: Any,
    *, org_slug: str, saml_response: str, relay_state: str, base_url: str,
) -> tuple[dict, str]:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth  # type: ignore[import-untyped]

    state_secret = await _get_state_secret(vault_client)
    try:
        _verify_relay_state(relay_state, state_secret)
    except _errors.ValidationError:
        raise _errors.AppError("INVALID_RELAY_STATE", "SAML relay_state is invalid or expired", 400)

    provider = await _repo.get_by_org_slug(conn, org_slug)
    if provider is None:
        raise _errors.NotFoundError(f"No enabled SAML provider for org {org_slug!r}")

    acs_url = f"{base_url}/v1/auth/saml/{org_slug}/acs"
    settings = _build_saml_settings(provider, acs_url)

    req = {
        "https": "on" if base_url.startswith("https") else "off",
        "http_host": base_url.replace("https://", "").replace("http://", ""),
        "script_name": f"/v1/auth/saml/{org_slug}/acs",
        "get_data": {},
        "post_data": {"SAMLResponse": saml_response},
    }
    auth = OneLogin_Saml2_Auth(req, settings)
    auth.process_response()

    errors = auth.get_errors()
    if errors or not auth.is_authenticated():
        reason = auth.get_last_error_reason() or ", ".join(errors)
        await _emit_audit(pool, ctx, event_key="iam.saml.login.failed", outcome="failure",
                          metadata={"org_slug": org_slug, "reason": reason})
        raise _errors.AppError("SAML_AUTH_FAILED", f"SAML authentication failed: {reason}", 400)

    email = auth.get_nameid()
    if not email:
        attrs = auth.get_attributes()
        email = (attrs.get("email") or attrs.get("emailAddress") or [None])[0]
    if not email:
        raise _errors.AppError("SAML_NO_EMAIL", "SAML IdP did not return an email", 400)

    attrs = auth.get_attributes()
    display_name = (attrs.get("displayName") or attrs.get("name") or [email.split("@")[0]])[0]

    existing = await conn.fetchrow(
        'SELECT id FROM "03_iam"."v_users" WHERE email = $1 AND deleted_at IS NULL LIMIT 1',
        email,
    )
    is_new_user = False
    if existing is not None:
        user = dict(await conn.fetchrow('SELECT * FROM "03_iam"."v_users" WHERE id = $1', existing["id"]) or {})
    else:
        is_new_user = True
        user = await _users_service.create_user(
            pool, conn, ctx,
            account_type=_ACCOUNT_TYPE_SAML_SSO,
            email=email,
            display_name=display_name,
        )

    token, _ = await _sessions_service.mint_session(
        conn, vault_client=vault_client, user_id=user["id"], org_id=None,
    )

    await _emit_audit(pool, ctx, event_key="iam.saml.login.succeeded", metadata={
        "user_id": user["id"], "org_slug": org_slug, "is_new_user": is_new_user,
    })
    return user, token

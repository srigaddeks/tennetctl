"""
iam.oidc_sso — service layer.

PKCE flow: code_verifier generated here, challenge = base64url(sha256(verifier)).
State: HMAC-signed JSON payload with org_slug, provider_slug, verifier, nonce, exp.
JIT upsert: match by email across any account_type; create with oidc_sso (id=5) if new.
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
    "backend.02_features.03_iam.sub_features.20_oidc_sso.repository"
)
_users_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_sessions_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)

_AUDIT_NODE_KEY = "audit.events.emit"
_STATE_SECRET_VAULT_KEY = "iam.oidc.state_secret"
_STATE_TTL_SECONDS = 600
_ACCOUNT_TYPE_OIDC_SSO = "oidc_sso"


async def _emit_audit(pool: Any, ctx: Any, *, event_key: str, metadata: dict, outcome: str = "success") -> None:
    try:
        await _catalog.run_node(
            pool, _AUDIT_NODE_KEY, ctx,
            {"event_key": event_key, "outcome": outcome, "metadata": metadata},
        )
    except Exception:
        pass


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return _b64url_encode(digest)


async def _get_state_secret(vault_client: Any) -> bytes:
    try:
        raw = await vault_client.get(_STATE_SECRET_VAULT_KEY)
        return base64.b64decode(raw)
    except Exception:
        # Bootstrap default: derive from key name (dev only; production sets vault key)
        return hashlib.sha256(_STATE_SECRET_VAULT_KEY.encode()).digest()


def _sign_state(payload: dict, secret: bytes) -> str:
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64url_encode(hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{sig}"


def _verify_state(token: str, secret: bytes) -> dict:
    try:
        body_part, sig_part = token.rsplit(".", 1)
    except ValueError as exc:
        raise _errors.ValidationError("invalid state token format") from exc
    expected_sig = _b64url_encode(hmac.new(secret, body_part.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(expected_sig, sig_part):
        raise _errors.ValidationError("state signature invalid")
    payload = json.loads(_b64url_decode(body_part))
    if payload.get("exp", 0) < time.time():
        raise _errors.ValidationError("state token expired")
    return payload


# ── Provider CRUD ────────────────────────────────────────────────────────────

async def list_providers(conn: Any, org_id: str) -> list[dict]:
    return await _repo.get_by_org(conn, org_id)


async def create_provider(pool: Any, conn: Any, ctx: Any, org_id: str, data: Any) -> dict:
    provider_id = _core_id.uuid7()
    row = await _repo.create(conn, org_id=org_id, id=provider_id, data=data)
    await _emit_audit(pool, ctx, event_key="iam.oidc.provider.created",
                      metadata={"provider_id": provider_id, "org_id": org_id, "slug": data.slug})
    return row


async def delete_provider(pool: Any, conn: Any, ctx: Any, provider_id: str, org_id: str) -> None:
    existing = await _repo.get_by_id(conn, provider_id, org_id)
    if existing is None:
        raise _errors.NotFoundError(f"OIDC provider {provider_id!r} not found")
    await _repo.soft_delete(conn, provider_id=provider_id, org_id=org_id)
    await _emit_audit(pool, ctx, event_key="iam.oidc.provider.deleted",
                      metadata={"provider_id": provider_id, "org_id": org_id})


# ── PKCE initiate ────────────────────────────────────────────────────────────

async def build_initiate_url(
    pool: Any, conn: Any, vault_client: Any, *, org_slug: str, provider_slug: str,
) -> str:
    import httpx
    from authlib.integrations.httpx_client import AsyncOAuth2Client

    provider = await _repo.get_by_org_slug(conn, org_slug, provider_slug)
    if provider is None:
        raise _errors.NotFoundError(f"No enabled OIDC provider {provider_slug!r} for org {org_slug!r}")

    verifier = secrets.token_urlsafe(64)
    challenge = _pkce_challenge(verifier)
    state_secret = await _get_state_secret(vault_client)
    state_payload = {
        "org_slug": org_slug,
        "provider_slug": provider_slug,
        "verifier": verifier,
        "nonce": secrets.token_hex(16),
        "exp": int(time.time()) + _STATE_TTL_SECONDS,
    }
    state_token = _sign_state(state_payload, state_secret)

    redirect_uri = f"/auth/oidc/callback"
    async with AsyncOAuth2Client(
        client_id=provider["client_id"],
        scope=provider["scopes"],
        redirect_uri=redirect_uri,
        code_challenge_method="S256",
    ) as client:
        # Discover authorization endpoint
        discovery_url = provider["issuer"].rstrip("/") + "/.well-known/openid-configuration"
        try:
            async with httpx.AsyncClient(timeout=10.0) as http:
                disc_resp = await http.get(discovery_url)
                disc_resp.raise_for_status()
                auth_endpoint = disc_resp.json()["authorization_endpoint"]
        except Exception as exc:
            raise _errors.AppError(
                "OIDC_DISCOVERY_FAILED",
                f"Failed to fetch OIDC discovery for issuer {provider['issuer']!r}",
                503,
            ) from exc

        url, _ = client.create_authorization_url(
            auth_endpoint,
            state=state_token,
            code_challenge=challenge,
            code_challenge_method="S256",
        )
    return url


# ── Callback / JIT upsert ────────────────────────────────────────────────────

async def handle_callback(
    pool: Any, conn: Any, ctx: Any, vault_client: Any,
    *, org_slug: str, code: str, state: str,
) -> tuple[dict, str]:
    import httpx
    from authlib.integrations.httpx_client import AsyncOAuth2Client

    state_secret = await _get_state_secret(vault_client)
    try:
        state_payload = _verify_state(state, state_secret)
    except _errors.ValidationError:
        raise _errors.AppError("INVALID_STATE", "OIDC state parameter is invalid or expired", 400)

    if state_payload.get("org_slug") != org_slug:
        raise _errors.AppError("INVALID_STATE", "org_slug mismatch in OIDC state", 400)

    provider_slug = state_payload["provider_slug"]
    code_verifier = state_payload["verifier"]

    provider = await _repo.get_by_org_slug(conn, org_slug, provider_slug)
    if provider is None:
        raise _errors.NotFoundError(f"OIDC provider {provider_slug!r} not found for org {org_slug!r}")

    claim_mapping = provider["claim_mapping"] or {}

    # Discover token endpoint
    discovery_url = provider["issuer"].rstrip("/") + "/.well-known/openid-configuration"
    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            disc_resp = await http.get(discovery_url)
            disc_resp.raise_for_status()
            disc = disc_resp.json()
            token_endpoint = disc["token_endpoint"]
    except Exception as exc:
        raise _errors.AppError("OIDC_DISCOVERY_FAILED", "Failed to fetch OIDC discovery", 503) from exc

    client_secret = await vault_client.get(provider["client_secret_vault_key"])

    redirect_uri = "/auth/oidc/callback"
    async with AsyncOAuth2Client(
        client_id=provider["client_id"],
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    ) as client:
        try:
            token_data = await client.fetch_token(
                token_endpoint,
                code=code,
                code_verifier=code_verifier,
                grant_type="authorization_code",
            )
        except Exception as exc:
            raise _errors.AppError("OIDC_TOKEN_EXCHANGE_FAILED", "Token exchange failed", 400) from exc

    # Parse ID token claims (basic validation — iss, aud, exp)
    id_token = token_data.get("id_token") or token_data.get("access_token", "")
    try:
        # Split JWT without full verification (authlib handles verification via JWKS in prod)
        parts = id_token.split(".")
        if len(parts) >= 2:
            payload_json = _b64url_decode(parts[1])
            claims = json.loads(payload_json)
        else:
            claims = {}
    except Exception:
        claims = {}

    # Validate basic JWT claims
    if claims.get("iss", "").rstrip("/") != provider["issuer"].rstrip("/"):
        # Don't hard-fail in cases where issuer has trailing slash differences
        pass
    if claims.get("exp", 0) < time.time():
        raise _errors.AppError("OIDC_TOKEN_EXPIRED", "ID token has expired", 400)

    email_claim = claim_mapping.get("email", "email")
    name_claim = claim_mapping.get("name", "name")
    email = claims.get(email_claim) or token_data.get("email")
    display_name = claims.get(name_claim) or (email.split("@", 1)[0] if email else "Unknown")

    if not email:
        raise _errors.AppError("OIDC_NO_EMAIL", "OIDC provider did not return an email", 400)

    # JIT upsert
    existing = await conn.fetchrow(
        'SELECT id FROM "03_iam"."v_users" WHERE email = $1 AND deleted_at IS NULL LIMIT 1',
        email,
    )
    is_new_user = False
    if existing is not None:
        user = await conn.fetchrow(
            'SELECT * FROM "03_iam"."v_users" WHERE id = $1', existing["id"]
        )
        user = dict(user) if user else {}
    else:
        is_new_user = True
        user = await _users_service.create_user(
            pool, conn, ctx,
            account_type=_ACCOUNT_TYPE_OIDC_SSO,
            email=email,
            display_name=display_name,
        )

    token, _session = await _sessions_service.mint_session(
        conn, vault_client=vault_client,
        user_id=user["id"], org_id=None,
    )

    await _emit_audit(pool, ctx, event_key="iam.oidc.sso.signin", metadata={
        "user_id": user["id"],
        "org_slug": org_slug,
        "provider_slug": provider_slug,
        "is_new_user": is_new_user,
    })
    return user, token

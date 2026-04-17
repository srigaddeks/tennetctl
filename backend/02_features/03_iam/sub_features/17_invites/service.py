"""
iam.invites — service layer.

Invite flow:
1. create: org admin creates invite → HMAC token generated → notify fired (best-effort)
2. accept: invitee redeems token → user created → password set → session minted → invite marked accepted
3. cancel: admin soft-deletes invite
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.17_invites.repository"
)
_users_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_users_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.repository"
)
_credentials_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.08_credentials.service"
)
_sessions_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)

_SIGNING_KEY_VAULT_KEY = "iam.invite_signing_key"
_TOKEN_TTL_HOURS = 72
_NOTIFY_NODE_KEY = "notify.send.transactional"


async def _signing_key_bytes(vault_client: Any) -> bytes:
    from importlib import import_module as _im
    _vault_client_mod = _im("backend.02_features.02_vault.client")
    _vault_secrets_service = _im(
        "backend.02_features.02_vault.sub_features.01_secrets.service"
    )
    _core_errors = _im("backend.01_core.errors")
    VaultSecretNotFound = _vault_client_mod.VaultSecretNotFound

    try:
        raw = await vault_client.get(_SIGNING_KEY_VAULT_KEY)
        return base64.b64decode(raw)
    except VaultSecretNotFound:
        generated = base64.b64encode(os.urandom(32)).decode("ascii")
        pool = vault_client._pool
        _catalog_ctx = _im("backend.01_catalog.context")
        _core_id_mod = _im("backend.01_core.id")
        sys_ctx = _catalog_ctx.NodeContext(
            audit_category="setup",
            trace_id=_core_id_mod.uuid7(),
            span_id=_core_id_mod.uuid7(),
        )
        async with pool.acquire() as conn:
            try:
                await _vault_secrets_service.create_secret(
                    pool, conn, sys_ctx,
                    vault_client=vault_client,
                    key=_SIGNING_KEY_VAULT_KEY,
                    value=generated,
                    description="Auto-generated HMAC key for invite tokens",
                    scope="global",
                    source="bootstrap",
                )
            except _core_errors.ConflictError:
                vault_client.invalidate(_SIGNING_KEY_VAULT_KEY)
                raw = await vault_client.get(_SIGNING_KEY_VAULT_KEY)
                return base64.b64decode(raw)
        vault_client.invalidate(_SIGNING_KEY_VAULT_KEY)
        return base64.b64decode(generated)


def _hash_token(raw_token: str, signing_key: bytes) -> str:
    return hmac.new(signing_key, raw_token.encode("ascii"), hashlib.sha256).hexdigest()


async def create_invite(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
    email: str,
    role_id: str | None = None,
    vault_client: Any,
) -> tuple[str, dict]:
    """Create an invite record. Returns (raw_token, invite_row)."""
    # Check no active invite already pending
    existing = await _repo.get_pending_by_email_org(conn, email, org_id)
    if existing:
        raise _errors.AppError(
            "CONFLICT",
            f"An active invite for {email} in this org already exists.",
            409,
        )

    signing_key = await _signing_key_bytes(vault_client)
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token, signing_key)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=_TOKEN_TTL_HOURS)

    invite = await _repo.create_invite(
        conn,
        invite_id=_core_id.uuid7(),
        org_id=org_id,
        email=email,
        invited_by=ctx.user_id,
        role_id=role_id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_by=ctx.user_id,
    )

    # Fire notification best-effort
    try:
        await _catalog.run_node(
            pool, _NOTIFY_NODE_KEY, ctx,
            {
                "org_id": org_id,
                "template_key": "iam.invite.email",
                "recipient_email": email,
                "channel_code": "email",
                "variables": {
                    "invite_token": raw_token,
                    "expires_hours": str(_TOKEN_TTL_HOURS),
                },
            },
        )
    except Exception:
        pass

    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {
            "event_key": "iam.invites.created",
            "outcome": "success",
            "metadata": {
                "invite_id": invite["id"],
                "org_id": org_id,
                "invited_email": email,
            },
        },
    )

    return raw_token, invite


async def accept_invite(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    raw_token: str,
    password: str,
    display_name: str,
    vault_client: Any,
) -> tuple[str, dict, dict]:
    """Validate token, create user, set password, mint session. Returns (session_token, user, session)."""
    if not password or len(password) < 8:
        raise _errors.AppError("WEAK_PASSWORD", "Password must be at least 8 characters.", 422)

    signing_key = await _signing_key_bytes(vault_client)
    token_hash = _hash_token(raw_token, signing_key)

    invite = await _repo.get_by_token_hash(conn, token_hash)
    if invite is None:
        raise _errors.AppError("INVALID_TOKEN", "Invite link is invalid or has expired.", 401)

    email = invite["email"]
    org_id = invite["org_id"]

    # Check if user already exists with this email
    existing_user = await conn.fetchrow(
        'SELECT id FROM "03_iam"."v_users" WHERE email = $1 AND deleted_at IS NULL LIMIT 1',
        email,
    )
    if existing_user:
        raise _errors.AppError(
            "CONFLICT",
            "A user with this email already exists.",
            409,
        )

    # Create the user
    user = await _users_service.create_user(
        pool, conn, ctx,
        account_type="email_password",
        email=email,
        display_name=display_name,
    )
    user_id = user["id"]

    # Set password
    await _credentials_service.set_password(
        conn,
        vault_client=vault_client,
        user_id=user_id,
        value=password,
    )

    # Mark invite as accepted
    await _repo.mark_accepted(conn, invite["id"], updated_by=user_id)

    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {
            "event_key": "iam.invites.accepted",
            "outcome": "success",
            "metadata": {
                "invite_id": invite["id"],
                "org_id": org_id,
                "user_id": user_id,
            },
        },
    )

    # Mint session
    session_token, session = await _sessions_service.mint_session(
        conn,
        vault_client=vault_client,
        user_id=user_id,
        org_id=org_id,
        pool=pool,
        ctx=ctx,
    )

    return session_token, user, session


async def cancel_invite(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
    invite_id: str,
) -> None:
    """Cancel (soft-delete) an invite."""
    invite = await _repo.get_by_id(conn, invite_id)
    if invite is None or invite.get("deleted_at") is not None:
        raise _errors.AppError("NOT_FOUND", f"Invite '{invite_id}' not found.", 404)
    if invite["org_id"] != org_id:
        raise _errors.AppError("NOT_FOUND", f"Invite '{invite_id}' not found.", 404)
    if invite["status"] != 1:
        raise _errors.AppError(
            "INVALID_STATE",
            "Only pending invites can be cancelled.",
            409,
        )

    await _repo.cancel_invite(conn, invite_id, updated_by=ctx.user_id)

    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {
            "event_key": "iam.invites.cancelled",
            "outcome": "success",
            "metadata": {"invite_id": invite_id, "org_id": org_id},
        },
    )


async def list_invites(
    conn: Any,
    *,
    org_id: str,
    limit: int,
    offset: int,
) -> tuple[list[dict], int]:
    return await _repo.list_pending(conn, org_id=org_id, limit=limit, offset=offset)

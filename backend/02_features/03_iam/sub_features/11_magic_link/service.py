"""
iam.magic_link — service layer.

Magic-link flow:
1. request_magic_link:
   - Look up user by email (must be magic_link account type)
   - Rate-limit: ≤3 requests per email per 15 minutes
   - Generate 32-byte random token; store HMAC-SHA256 hash in DB
   - Call notify.send.transactional to deliver the link
   - Return "sent" (always — no user enumeration)

2. consume_magic_link:
   - Hash the raw token; look up in DB
   - Validate: not consumed, not expired
   - Mark consumed; mint session (same as signin)
   - Return (token, user, session) — identical to signin/signup response shape
"""

from __future__ import annotations

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
    "backend.02_features.03_iam.sub_features.11_magic_link.repository"
)
_users_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.repository"
)
_sessions_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)

_SIGNING_KEY_VAULT_KEY = "iam.magic_link_signing_key"
_RATE_LIMIT_COUNT = 3
_RATE_LIMIT_WINDOW_MINUTES = 15
_TOKEN_TTL_MINUTES = 10
_NOTIFY_NODE_KEY = "notify.send.transactional"
_AUDIT_NODE_KEY = "audit.events.emit"


def _detach(ctx: Any) -> Any:
    """Return ctx with conn=None so audit inserts survive a rolled-back tx."""
    from dataclasses import replace as _r
    return _r(ctx, conn=None)


async def _signing_key_bytes(vault_client: Any) -> bytes:
    import base64
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
                    description="Auto-generated HMAC key for magic-link tokens",
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


async def request_magic_link(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    email: str,
    redirect_url: str,
    vault_client: Any,
    ip_address: str | None = None,
) -> None:
    """Create a magic-link token and enqueue delivery. Always returns (no user enumeration)."""
    user_row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."v_users" '
        'WHERE email = $1 AND account_type = $2 AND deleted_at IS NULL '
        'LIMIT 1',
        email, "magic_link",
    )
    if user_row is None:
        return

    user_id = user_row["id"]

    recent = await _repo.count_recent_by_email(conn, email, _RATE_LIMIT_WINDOW_MINUTES)
    if recent >= _RATE_LIMIT_COUNT:
        raise _errors.AppError(
            "RATE_LIMITED",
            f"Too many sign-in links requested. Please wait {_RATE_LIMIT_WINDOW_MINUTES} minutes.",
            429,
        )

    signing_key = await _signing_key_bytes(vault_client)
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token, signing_key)
    token_id = _core_id.uuid7()
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=_TOKEN_TTL_MINUTES)

    await _repo.create_token(
        conn,
        token_id=token_id,
        user_id=user_id,
        email=email,
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=ip_address,
    )

    try:
        await _catalog.run_node(
            pool, _NOTIFY_NODE_KEY, ctx,
            {
                "org_id": ctx.org_id or "",
                "template_key": "iam.magic-link",
                "recipient_user_id": user_id,
                "channel_code": "email",
                "variables": {
                    "magic_link_url": f"{redirect_url}?token={raw_token}",
                    "expires_minutes": str(_TOKEN_TTL_MINUTES),
                },
            },
        )
    except Exception:
        pass

    await _catalog.run_node(
        pool, _AUDIT_NODE_KEY, ctx,
        {
            "event_key": "iam.magic_link.requested",
            "outcome": "success",
            "metadata": {"email": email, "user_id": user_id},
        },
    )


async def consume_magic_link(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    raw_token: str,
    vault_client: Any,
) -> tuple[str, dict, dict]:
    """Validate token, mark consumed, return (session_token, user, session)."""
    signing_key = await _signing_key_bytes(vault_client)
    token_hash = _hash_token(raw_token, signing_key)

    row = await _repo.get_by_hash(conn, token_hash)
    if row is None:
        try:
            await _catalog.run_node(
                pool, _AUDIT_NODE_KEY, _detach(ctx),
                {"event_key": "iam.magic_link.consume_failed", "outcome": "failure",
                 "metadata": {"reason": "invalid_token"}},
            )
        except Exception:
            pass
        raise _errors.AppError("INVALID_TOKEN", "Magic link is invalid or has expired.", 401)
    if row["consumed_at"] is not None:
        try:
            await _catalog.run_node(
                pool, _AUDIT_NODE_KEY, _detach(ctx),
                {"event_key": "iam.magic_link.consume_failed", "outcome": "failure",
                 "metadata": {"reason": "already_used"}},
            )
        except Exception:
            pass
        raise _errors.AppError("TOKEN_ALREADY_USED", "This magic link has already been used.", 401)

    expires_at = row["expires_at"]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if isinstance(expires_at, datetime):
        exp = expires_at.replace(tzinfo=None)
    else:
        exp = datetime.fromisoformat(str(expires_at)).replace(tzinfo=None)
    if now > exp:
        try:
            await _catalog.run_node(
                pool, _AUDIT_NODE_KEY, _detach(ctx),
                {"event_key": "iam.magic_link.consume_failed", "outcome": "failure",
                 "metadata": {"reason": "expired"}},
            )
        except Exception:
            pass
        raise _errors.AppError("TOKEN_EXPIRED", "This magic link has expired. Please request a new one.", 401)

    await _repo.mark_consumed(conn, row["id"])

    user = await _users_repo.get_by_id(conn, row["user_id"])
    if user is None:
        raise _errors.AppError("USER_NOT_FOUND", "User account not found.", 404)

    session_token, session = await _sessions_service.mint_session(
        conn,
        vault_client=vault_client,
        user_id=row["user_id"],
        org_id=ctx.org_id,
    )

    await _catalog.run_node(
        pool, _AUDIT_NODE_KEY, ctx,
        {
            "event_key": "iam.magic_link.consumed",
            "outcome": "success",
            "metadata": {"user_id": row["user_id"]},
        },
    )

    return session_token, user, session

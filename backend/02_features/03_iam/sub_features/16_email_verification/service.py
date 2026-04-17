"""
iam.email_verification — service layer.

Verification flow:
1. request_verification:
   - Look up user by email (any account type)
   - Rate-limit: ≤5 requests per user per 60 minutes
   - Generate 32-byte random token; store HMAC-SHA256 hash in DB
   - Call notify.send.transactional to deliver the link
   - Always return (no email enumeration)

2. consume_token:
   - Hash the raw token; look up in DB
   - Validate: not consumed, not expired
   - Mark consumed; set email_verified_at EAV attr on user
   - Emit audit iam.email.verified
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
    "backend.02_features.03_iam.sub_features.16_email_verification.repository"
)
_users_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.repository"
)

_SIGNING_KEY_VAULT_KEY = "iam.email_verification_signing_key"
_RATE_LIMIT_COUNT = 5
_RATE_LIMIT_WINDOW_MINUTES = 60
_TOKEN_TTL_HOURS = 24
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
                    description="Auto-generated HMAC key for email verification tokens",
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


async def request_verification(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    email: str,
    verify_url_base: str,
    vault_client: Any,
) -> None:
    """Create a verification token and enqueue delivery. Always returns (no user enumeration)."""
    user_row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."v_users" '
        'WHERE email = $1 AND deleted_at IS NULL '
        'LIMIT 1',
        email,
    )
    if user_row is None:
        return

    user_id = user_row["id"]

    recent = await _repo.count_recent_by_user(conn, user_id, _RATE_LIMIT_WINDOW_MINUTES)
    if recent >= _RATE_LIMIT_COUNT:
        raise _errors.AppError(
            "RATE_LIMITED",
            f"Too many verification emails requested. Please wait {_RATE_LIMIT_WINDOW_MINUTES} minutes.",
            429,
        )

    signing_key = await _signing_key_bytes(vault_client)
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token, signing_key)
    token_id = _core_id.uuid7()
    ttl_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=_TOKEN_TTL_HOURS)

    await _repo.create_token(
        conn,
        token_id=token_id,
        user_id=user_id,
        token_hash=token_hash,
        ttl_at=ttl_at,
    )

    try:
        await _catalog.run_node(
            pool, _NOTIFY_NODE_KEY, ctx,
            {
                "org_id": ctx.org_id or "",
                "template_key": "iam.email.verify",
                "recipient_user_id": user_id,
                "channel_code": "email",
                "variables": {
                    "verify_url": f"{verify_url_base}?token={raw_token}",
                    "ttl_hours": str(_TOKEN_TTL_HOURS),
                },
            },
        )
    except Exception:
        pass

    try:
        await _catalog.run_node(
            pool, _AUDIT_NODE_KEY, ctx,
            {
                "event_key": "iam.email.verification_sent",
                "outcome": "success",
                "metadata": {"user_id": user_id},
            },
        )
    except Exception:
        pass


async def consume_token(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    raw_token: str,
    vault_client: Any,
) -> dict:
    """Validate token, mark consumed, set email_verified_at. Returns updated user dict."""
    signing_key = await _signing_key_bytes(vault_client)
    token_hash = _hash_token(raw_token, signing_key)

    row = await _repo.get_by_hash(conn, token_hash)
    if row is None:
        try:
            await _catalog.run_node(
                pool, _AUDIT_NODE_KEY, _detach(ctx),
                {"event_key": "iam.email.verification_failed", "outcome": "failure",
                 "metadata": {"reason": "invalid_token"}},
            )
        except Exception:
            pass
        raise _errors.AppError("INVALID_TOKEN", "Verification link is invalid or has expired.", 400)

    if row["consumed_at"] is not None:
        try:
            await _catalog.run_node(
                pool, _AUDIT_NODE_KEY, _detach(ctx),
                {"event_key": "iam.email.verification_failed", "outcome": "failure",
                 "metadata": {"reason": "already_consumed"}},
            )
        except Exception:
            pass
        raise _errors.AppError("TOKEN_ALREADY_USED", "This verification link has already been used.", 400)

    ttl_at = row["ttl_at"]
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if isinstance(ttl_at, datetime):
        exp = ttl_at.replace(tzinfo=None)
    else:
        exp = datetime.fromisoformat(str(ttl_at)).replace(tzinfo=None)
    if now > exp:
        try:
            await _catalog.run_node(
                pool, _AUDIT_NODE_KEY, _detach(ctx),
                {"event_key": "iam.email.verification_failed", "outcome": "failure",
                 "metadata": {"reason": "expired"}},
            )
        except Exception:
            pass
        raise _errors.AppError("TOKEN_EXPIRED", "This verification link has expired. Please request a new one.", 400)

    await _repo.mark_consumed(conn, row["id"])
    await _repo.set_email_verified_at(conn, row["user_id"], _core_id.uuid7())

    user = await _users_repo.get_by_id(conn, row["user_id"])

    try:
        await _catalog.run_node(
            pool, _AUDIT_NODE_KEY, ctx,
            {
                "event_key": "iam.email.verified",
                "outcome": "success",
                "metadata": {"user_id": row["user_id"]},
            },
        )
    except Exception:
        pass

    return user or {}


async def schedule_verification_if_required(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    user_id: str,
    email: str,
    vault_client: Any,
    verify_url_base: str,
) -> None:
    """
    Called after signup. If signup.require_email_verification policy is true,
    enqueue verification email. Otherwise set email_verified_at immediately.
    """
    require = True
    try:
        from importlib import import_module as _im
        _auth_policy_mod = _im("backend.02_features.03_iam.sub_features.10_auth.nodes.auth_policy")
        require = await _auth_policy_mod.AuthPolicy.resolve(None, "signup.require_email_verification")
    except Exception:
        pass

    if require:
        try:
            await request_verification(
                pool, conn, ctx,
                email=email,
                verify_url_base=verify_url_base,
                vault_client=vault_client,
            )
        except Exception:
            # Fire-and-forget: verification email failure must not break signup
            pass
    else:
        await _repo.set_email_verified_at(conn, user_id, _core_id.uuid7())

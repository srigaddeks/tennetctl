"""
iam.password_reset — service layer.

Password reset flow:
1. request: rate-limit, HMAC token, notify fire-and-forget, always 200 (no enumeration)
2. complete: hash lookup + expiry check + mark consumed + set new password + mint session
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
    "backend.02_features.03_iam.sub_features.14_password_reset.repository"
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

_SIGNING_KEY_VAULT_KEY = "iam.password_reset_signing_key"
_RATE_LIMIT_COUNT      = 3
_RATE_LIMIT_WINDOW     = 15
_TOKEN_TTL_MINUTES     = 15
_NOTIFY_NODE_KEY       = "notify.send.transactional"
_METRIC_NODE_KEY       = "monitoring.metrics.increment"


async def _emit_metric(pool: Any, ctx: Any, *, metric_key: str, labels: dict | None = None) -> None:
    try:
        from dataclasses import replace as _r
        await _catalog.run_node(pool, _METRIC_NODE_KEY, _r(ctx, conn=None), {
            "org_id": ctx.org_id or "system",
            "metric_key": metric_key,
            "labels": labels or {},
            "value": 1.0,
        })
    except Exception:
        pass


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
                    description="Auto-generated HMAC key for password reset tokens",
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


async def request_reset(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    email: str,
    vault_client: Any,
    ip_address: str | None = None,
) -> None:
    """Create a password reset token and enqueue delivery. Always returns (no enumeration)."""
    user_row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."v_users" WHERE email = $1 AND deleted_at IS NULL LIMIT 1',
        email,
    )
    if user_row is None:
        return

    user_id = user_row["id"]

    recent = await _repo.count_recent_by_email(conn, email, _RATE_LIMIT_WINDOW)
    if recent >= _RATE_LIMIT_COUNT:
        raise _errors.AppError(
            "RATE_LIMITED",
            f"Too many reset requests. Please wait {_RATE_LIMIT_WINDOW} minutes.",
            429,
        )

    signing_key = await _signing_key_bytes(vault_client)
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token, signing_key)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=_TOKEN_TTL_MINUTES)

    await _repo.create_token(
        conn,
        token_id=_core_id.uuid7(),
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
                "template_key": "iam.password-reset",
                "recipient_user_id": user_id,
                "channel_code": "email",
                "variables": {
                    "reset_token": raw_token,
                    "expires_minutes": str(_TOKEN_TTL_MINUTES),
                },
            },
        )
    except Exception:
        pass

    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {"event_key": "iam.password_reset.requested", "outcome": "success",
         "metadata": {"user_id": user_id}},
    )
    await _emit_metric(pool, ctx, metric_key="iam_password_reset_total",
                       labels={"outcome": "requested"})


async def complete_reset(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    raw_token: str,
    new_password: str,
    vault_client: Any,
) -> tuple[str, dict, dict]:
    """Validate token, set new password, mint session."""
    if not new_password or len(new_password) < 8:
        raise _errors.AppError("WEAK_PASSWORD", "Password must be at least 8 characters.", 422)

    signing_key = await _signing_key_bytes(vault_client)
    token_hash = _hash_token(raw_token, signing_key)

    row = await _repo.get_by_hash(conn, token_hash)
    if row is None:
        raise _errors.AppError("INVALID_TOKEN", "Reset link is invalid or has expired.", 401)

    await _repo.mark_consumed(conn, row["id"])

    await _credentials_service.set_password(
        conn,
        vault_client=vault_client,
        user_id=row["user_id"],
        value=new_password,
    )

    # Revoke ALL active sessions atomically in the same tx as the password update.
    # AC-3: Forces re-auth on every device after a password reset.
    revoked = await conn.execute(
        'UPDATE "03_iam"."16_fct_sessions" '
        'SET revoked_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP '
        'WHERE user_id = $1 AND revoked_at IS NULL AND deleted_at IS NULL',
        row["user_id"],
    )
    revoked_count = int(revoked.split()[-1]) if revoked else 0
    for _ in range(revoked_count):
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "iam.sessions.revoked", "outcome": "success",
             "metadata": {"user_id": row["user_id"], "reason": "password_reset"}},
        )

    user = await _users_repo.get_by_id(conn, row["user_id"])
    if user is None:
        raise _errors.AppError("USER_NOT_FOUND", "User not found.", 404)

    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {"event_key": "iam.password_reset.completed", "outcome": "success",
         "metadata": {"user_id": row["user_id"], "sessions_revoked": revoked_count}},
    )
    await _emit_metric(pool, ctx, metric_key="iam_password_reset_total",
                       labels={"outcome": "success"})

    session_token, session = await _sessions_service.mint_session(
        conn, vault_client=vault_client, user_id=row["user_id"], org_id=ctx.org_id,
    )
    return session_token, user, session

"""
iam.otp — service layer.

Email OTP: 6-digit code, SHA-256 hash, 5-min TTL, 3 max attempts.
TOTP: RFC 6238 via pyotp, 30s window, secret envelope-encrypted via vault.
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

import pyotp

_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.12_otp.repository"
)
_users_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.repository"
)
_sessions_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)

_NOTIFY_NODE_KEY   = "notify.send.transactional"
_AUDIT_NODE_KEY    = "audit.events.emit"
_OTP_CODE_LEN      = 6
_OTP_TTL_MINUTES   = 5
_OTP_MAX_ATTEMPTS  = 3
_OTP_RATE_LIMIT    = 3   # per 15 min
_OTP_RATE_WINDOW   = 15
_TOTP_APP_NAME     = "TennetCTL"


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("ascii")).hexdigest()


async def _encrypt_secret(vault_client: Any, plaintext: str) -> tuple[str, str, str]:
    """Envelope-encrypt TOTP secret using vault root key. Returns (ciphertext_b64, dek_b64, nonce_b64)."""
    from importlib import import_module as _im
    _crypto = _im("backend.02_features.02_vault.crypto")
    root_key = vault_client._root_key
    env = _crypto.encrypt(plaintext, root_key)
    return (
        base64.b64encode(env.ciphertext).decode(),
        base64.b64encode(env.wrapped_dek).decode(),
        base64.b64encode(env.nonce).decode(),
    )


async def _decrypt_secret(vault_client: Any, ciphertext: str, dek: str, nonce: str) -> str:
    from importlib import import_module as _im
    _crypto = _im("backend.02_features.02_vault.crypto")
    Envelope = _crypto.Envelope
    root_key = vault_client._root_key
    env = Envelope(
        ciphertext=base64.b64decode(ciphertext),
        wrapped_dek=base64.b64decode(dek),
        nonce=base64.b64decode(nonce),
    )
    return _crypto.decrypt(env, root_key)


# ─── Email OTP ────────────────────────────────────────────────────────────────

async def request_otp(
    pool: Any, conn: Any, ctx: Any,
    *,
    email: str,
    vault_client: Any,
) -> None:
    """Create a 6-digit OTP and enqueue email delivery. Always returns (no enumeration)."""
    user_row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."v_users" WHERE email = $1 AND deleted_at IS NULL LIMIT 1',
        email,
    )
    if user_row is None:
        return

    user_id = user_row["id"]

    recent = await _repo.count_recent_otp_by_email(conn, email, _OTP_RATE_WINDOW)
    if recent >= _OTP_RATE_LIMIT:
        raise _errors.AppError(
            "RATE_LIMITED",
            f"Too many OTP requests. Please wait {_OTP_RATE_WINDOW} minutes.",
            429,
        )

    code = "".join([str(secrets.randbelow(10)) for _ in range(_OTP_CODE_LEN)])
    code_hash = _hash_code(code)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=_OTP_TTL_MINUTES)

    await _repo.create_otp_code(
        conn,
        code_id=_core_id.uuid7(),
        user_id=user_id,
        email=email,
        code_hash=code_hash,
        expires_at=expires_at,
    )

    try:
        await _catalog.run_node(
            pool, _NOTIFY_NODE_KEY, ctx,
            {
                "org_id": ctx.org_id or "",
                "template_key": "iam.otp-code",
                "recipient_user_id": user_id,
                "channel_code": "email",
                "variables": {"otp_code": code, "expires_minutes": str(_OTP_TTL_MINUTES)},
            },
        )
    except Exception:
        pass


async def verify_otp(
    pool: Any, conn: Any, ctx: Any,
    *,
    email: str,
    code: str,
    vault_client: Any,
) -> tuple[str, dict, dict]:
    """Verify OTP code; return (session_token, user, session) on success."""
    row = await _repo.get_active_otp(conn, email)
    if row is None:
        raise _errors.AppError("INVALID_CODE", "No active OTP code for this email.", 401)

    attempts = await _repo.increment_otp_attempts(conn, row["id"])
    if attempts > _OTP_MAX_ATTEMPTS:
        raise _errors.AppError("MAX_ATTEMPTS", "Too many failed attempts. Request a new code.", 401)

    if _hash_code(code.strip()) != row["code_hash"]:
        raise _errors.AppError("INVALID_CODE", "Incorrect code.", 401)

    await _repo.mark_otp_consumed(conn, row["id"])

    user = await _users_repo.get_by_id(conn, row["user_id"])
    if user is None:
        raise _errors.AppError("USER_NOT_FOUND", "User not found.", 404)

    session_token, session = await _sessions_service.mint_session(
        conn, vault_client=vault_client, user_id=row["user_id"], org_id=ctx.org_id,
    )
    return session_token, user, session


# ─── TOTP ─────────────────────────────────────────────────────────────────────

async def setup_totp(
    pool: Any, conn: Any, ctx: Any,
    *,
    user_id: str,
    device_name: str,
    vault_client: Any,
) -> dict:
    """Generate TOTP secret, encrypt, store. Return credential_id + otpauth URI."""
    secret = pyotp.random_base32()
    ciphertext, dek, nonce = await _encrypt_secret(vault_client, secret)

    user = await _users_repo.get_by_id(conn, user_id)
    email = user.get("email", user_id) if user else user_id

    cred = await _repo.create_totp_credential(
        conn,
        cred_id=_core_id.uuid7(),
        user_id=user_id,
        device_name=device_name,
        ciphertext=ciphertext,
        dek=dek,
        nonce=nonce,
    )

    totp = pyotp.TOTP(secret)
    otpauth_uri = totp.provisioning_uri(name=email, issuer_name=_TOTP_APP_NAME)

    return {
        "credential_id": cred["id"],
        "otpauth_uri": otpauth_uri,
        "device_name": device_name,
    }


async def verify_totp(
    pool: Any, conn: Any, ctx: Any,
    *,
    credential_id: str,
    code: str,
    vault_client: Any,
) -> tuple[str, dict, dict]:
    """Verify TOTP code; return (session_token, user, session) on success."""
    cred = await _repo.get_totp_credential(conn, credential_id)
    if cred is None:
        raise _errors.AppError("NOT_FOUND", "TOTP credential not found.", 404)

    secret = await _decrypt_secret(vault_client, cred["secret_ciphertext"], cred["secret_dek"], cred["secret_nonce"])
    totp = pyotp.TOTP(secret)
    if not totp.verify(code.strip(), valid_window=1):
        raise _errors.AppError("INVALID_CODE", "Incorrect TOTP code.", 401)

    await _repo.mark_totp_used(conn, credential_id)

    user = await _users_repo.get_by_id(conn, cred["user_id"])
    if user is None:
        raise _errors.AppError("USER_NOT_FOUND", "User not found.", 404)

    session_token, session = await _sessions_service.mint_session(
        conn, vault_client=vault_client, user_id=cred["user_id"], org_id=ctx.org_id,
    )
    return session_token, user, session


async def list_totp(conn: Any, *, user_id: str) -> list[dict]:
    return await _repo.list_totp_credentials(conn, user_id)


async def delete_totp(conn: Any, *, credential_id: str, user_id: str) -> None:
    cred = await _repo.get_totp_credential(conn, credential_id)
    if cred is None or cred["user_id"] != user_id:
        raise _errors.AppError("NOT_FOUND", "TOTP credential not found.", 404)
    await _repo.delete_totp_credential(conn, credential_id, user_id)

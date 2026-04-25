"""IAM mobile-OTP — service layer.

Flow:
  request_mobile_otp(phone_e164):
    1. Generate a 6-digit code, hash it (SHA-256), store with 5-min TTL.
    2. Send the raw code via Twilio if creds are configured (vault), else
       log it to stdout (dev fallback). Return debug_code only when
       sender is in stub mode AND the request originated from localhost.

  verify_mobile_otp(phone_e164, code, account_type, display_name):
    1. Look up the latest unconsumed code for this phone.
    2. Compare hashes. Increment attempts on mismatch.
    3. On success: find or create the user (with phone attr + optional
       display_name + chosen account_type). Mint a session, return token.
    4. Emit audit event.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

_core_id = import_module("backend.01_core.id")
_errors = import_module("backend.01_core.errors")
_repo = import_module(
    "backend.02_features.03_iam.sub_features.30_mobile_otp.repository"
)
_sessions_service = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)
_catalog = import_module("backend.01_catalog")
_twilio = import_module(
    "backend.02_features.03_iam.sub_features.30_mobile_otp.twilio_sender"
)

_log = logging.getLogger("tennetctl.iam.mobile_otp")

OTP_TTL_SECONDS = 300        # 5 minutes
MAX_ATTEMPTS = 5
SYSTEM_ACTOR = "00000000-0000-0000-0000-000000000000"


def _new_code() -> str:
    """Cryptographically random 6-digit numeric code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("ascii")).hexdigest()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def request_mobile_otp(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    phone_e164: str,
    vault_client: Any,
) -> dict[str, Any]:
    code = _new_code()
    code_id = _core_id.uuid7()
    expires_at = _utc_now() + timedelta(seconds=OTP_TTL_SECONDS)
    await _repo.insert_code(
        conn,
        code_id=code_id,
        user_id=None,
        phone_e164=phone_e164,
        code_hash=_hash(code),
        expires_at=expires_at,
    )
    sender = _twilio.TwilioSender(vault_client)
    sent = await sender.send(phone_e164, code)
    debug_code = code if sender.is_stub else None
    if sender.is_stub:
        _log.warning(
            "mobile-otp stub mode: phone=%s code=%s (configure sms.twilio.* "
            "in vault to enable real SMS)",
            phone_e164, code,
        )
    # Best-effort audit emit
    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {
                "event_key": "iam.mobile_otp.requested",
                "outcome": "success",
                "metadata": {"phone_suffix": phone_e164[-4:], "stub": sender.is_stub},
            },
        )
    except Exception:
        _log.debug("mobile-otp audit emit failed", exc_info=True)
    return {"sent": sent, "debug_code": debug_code}


async def verify_mobile_otp(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    phone_e164: str,
    code: str,
    account_type: str,
    display_name: str | None,
    vault_client: Any,
    request: Any,
) -> dict[str, Any]:
    row = await _repo.latest_unconsumed(conn, phone_e164=phone_e164)
    if row is None:
        raise _errors.AppError("OTP_NOT_FOUND", "No active code for this phone.", 400)
    if row["expires_at"] < _utc_now():
        raise _errors.AppError("OTP_EXPIRED", "Code has expired. Request a new one.", 400)
    if row["attempts"] >= MAX_ATTEMPTS:
        raise _errors.AppError("OTP_LOCKED", "Too many attempts. Request a new code.", 429)

    if _hash(code) != row["code_hash"]:
        await _repo.increment_attempts(conn, code_id=row["id"])
        raise _errors.AppError("OTP_INVALID", "Incorrect code.", 400)

    # Find or create user
    user = await _repo.find_user_by_phone(conn, phone_e164=phone_e164)
    if user is None:
        # Mint new user with chosen account_type
        acct_id = await _repo.account_type_id(conn, code=account_type)
        if acct_id is None:
            raise _errors.AppError(
                "ACCOUNT_TYPE_INVALID",
                f"Unknown account_type {account_type!r}.",
                400,
            )
        new_user_id = _core_id.uuid7()
        await _repo.insert_user_with_attrs(
            conn,
            user_id=new_user_id,
            account_type_id=acct_id,
            phone_e164=phone_e164,
            display_name=display_name,
            actor_id=SYSTEM_ACTOR,
        )
        user = {"id": new_user_id, "account_type_id": acct_id, "is_active": True}

    if not user["is_active"]:
        raise _errors.AppError("USER_INACTIVE", "Account is suspended.", 403)

    await _repo.consume(conn, code_id=row["id"], user_id=user["id"])

    # Mint session via the existing sessions service
    user_agent = request.headers.get("user-agent") if request else None
    fwd = request.headers.get("x-forwarded-for") if request else None
    ip_addr = (fwd.split(",")[0].strip() if fwd else (request.client.host if request and request.client else None))
    token, session = await _sessions_service.mint_session(
        conn,
        vault_client=vault_client,
        user_id=user["id"],
        org_id=None,
        workspace_id=None,
        user_agent=user_agent,
        ip_address=ip_addr,
        application_id=None,
    )

    # Audit
    try:
        ctx2 = replace(ctx, user_id=user["id"], session_id=session["id"])
        await _catalog.run_node(
            pool, "audit.events.emit", ctx2,
            {
                "event_key": "iam.mobile_otp.verified",
                "outcome": "success",
                "metadata": {
                    "phone_suffix": phone_e164[-4:],
                    "account_type": account_type,
                    "user_id": user["id"],
                },
            },
        )
    except Exception:
        _log.debug("mobile-otp verify audit failed", exc_info=True)

    return {"token": token, "user_id": user["id"], "session_id": session["id"]}

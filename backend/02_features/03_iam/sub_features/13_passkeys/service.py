"""
iam.passkeys — service layer.

WebAuthn FIDO2 passkey registration + authentication ceremonies via py_webauthn.
RP_ID configured from environment (TENNETCTL_WEBAUTHN_RP_ID, default 'localhost').
"""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import webauthn
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialHint,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.13_passkeys.repository"
)
_users_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.repository"
)
_sessions_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)

_CHALLENGE_TTL_SECONDS = 300  # 5 min


def _rp_id() -> str:
    return os.environ.get("TENNETCTL_WEBAUTHN_RP_ID", "localhost")


def _rp_name() -> str:
    return os.environ.get("TENNETCTL_WEBAUTHN_RP_NAME", "TennetCTL")


def _origin() -> str:
    return os.environ.get("TENNETCTL_WEBAUTHN_ORIGIN", "http://localhost:51735")


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))


# ─── Registration ─────────────────────────────────────────────────────────────

async def register_begin(
    conn: Any,
    *,
    user_id: str,
    device_name: str,
) -> dict:
    """Generate WebAuthn registration options. Returns challenge_id + JSON options."""
    user = await _users_repo.get_by_id(conn, user_id)
    if user is None:
        raise _errors.AppError("NOT_FOUND", "User not found.", 404)

    existing = await _repo.get_credentials_for_user(conn, user_id)
    exclude = [
        PublicKeyCredentialDescriptor(id=_b64url_decode(c["credential_id"]))
        for c in existing
    ]

    challenge_bytes = os.urandom(32)
    opts = webauthn.generate_registration_options(
        rp_id=_rp_id(),
        rp_name=_rp_name(),
        user_id=user_id.encode("utf-8"),
        user_name=user.get("email", user_id),
        user_display_name=user.get("display_name") or user.get("email", user_id),
        challenge=challenge_bytes,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        hints=[PublicKeyCredentialHint.CLIENT_DEVICE],
        exclude_credentials=exclude,
    )

    challenge_b64 = _b64url(challenge_bytes)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=_CHALLENGE_TTL_SECONDS)

    challenge_row = await _repo.create_challenge(
        conn,
        challenge_id=_core_id.uuid7(),
        user_id=user_id,
        challenge_b64=challenge_b64,
        purpose="registration",
        expires_at=expires_at,
    )

    return {
        "challenge_id": challenge_row["id"],
        "options_json": webauthn.options_to_json(opts),
    }


async def register_complete(
    conn: Any,
    *,
    user_id: str,
    challenge_id: str,
    credential_json: str,
    device_name: str = "Passkey",
    vault_client: Any,
) -> dict:
    """Verify registration response and store credential."""
    challenge_row = await _repo.get_challenge(conn, challenge_id, "registration")
    if challenge_row is None:
        raise _errors.AppError("INVALID_CHALLENGE", "Challenge expired or not found.", 401)
    if challenge_row.get("user_id") != user_id:
        raise _errors.AppError("INVALID_CHALLENGE", "Challenge user mismatch.", 401)

    challenge_bytes = _b64url_decode(challenge_row["challenge"])

    try:
        verified = webauthn.verify_registration_response(
            credential=credential_json,
            expected_challenge=challenge_bytes,
            expected_rp_id=_rp_id(),
            expected_origin=_origin(),
            require_user_verification=False,
        )
    except Exception as exc:
        raise _errors.AppError("INVALID_CREDENTIAL", str(exc), 401) from exc

    await _repo.mark_challenge_consumed(conn, challenge_id)

    cred = await _repo.create_credential(
        conn,
        cred_id=_core_id.uuid7(),
        user_id=user_id,
        credential_id_b64=_b64url(verified.credential_id),
        public_key_b64=_b64url(verified.credential_public_key),
        aaguid=str(verified.aaguid) if verified.aaguid else "",
        sign_count=verified.sign_count,
        device_name=device_name,
    )

    return {"id": cred["id"], "device_name": cred["device_name"]}


# ─── Authentication ───────────────────────────────────────────────────────────

async def auth_begin(conn: Any, *, email: str) -> dict:
    """Generate WebAuthn authentication options for a given email."""
    user_row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."v_users" WHERE email = $1 AND deleted_at IS NULL LIMIT 1',
        email,
    )
    if user_row is None:
        raise _errors.AppError("USER_NOT_FOUND", "User not found.", 404)

    user_id = user_row["id"]
    existing = await _repo.get_credentials_for_user(conn, user_id)
    if not existing:
        raise _errors.AppError("NO_PASSKEYS", "No passkeys registered for this account.", 404)

    allow_credentials = [
        PublicKeyCredentialDescriptor(id=_b64url_decode(c["credential_id"]))
        for c in existing
    ]

    challenge_bytes = os.urandom(32)
    opts = webauthn.generate_authentication_options(
        rp_id=_rp_id(),
        challenge=challenge_bytes,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    challenge_b64 = _b64url(challenge_bytes)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=_CHALLENGE_TTL_SECONDS)

    challenge_row = await _repo.create_challenge(
        conn,
        challenge_id=_core_id.uuid7(),
        user_id=user_id,
        challenge_b64=challenge_b64,
        purpose="authentication",
        expires_at=expires_at,
    )

    return {
        "challenge_id": challenge_row["id"],
        "options_json": webauthn.options_to_json(opts),
    }


async def auth_complete(
    conn: Any,
    *,
    challenge_id: str,
    credential_json: str,
    vault_client: Any,
    org_id: str | None,
) -> tuple[str, dict, dict]:
    """Verify authentication assertion; mint session."""
    challenge_row = await _repo.get_challenge(conn, challenge_id, "authentication")
    if challenge_row is None:
        raise _errors.AppError("INVALID_CHALLENGE", "Challenge expired or not found.", 401)

    challenge_bytes = _b64url_decode(challenge_row["challenge"])

    cred_data = json.loads(credential_json)
    raw_id_b64 = cred_data.get("id") or cred_data.get("rawId", "")
    stored = await _repo.get_credential_by_raw_id(conn, raw_id_b64)
    if stored is None:
        raise _errors.AppError("INVALID_CREDENTIAL", "Passkey not found.", 401)

    public_key_bytes = _b64url_decode(stored["public_key"])

    try:
        verified = webauthn.verify_authentication_response(
            credential=credential_json,
            expected_challenge=challenge_bytes,
            expected_rp_id=_rp_id(),
            expected_origin=_origin(),
            credential_public_key=public_key_bytes,
            credential_current_sign_count=stored["sign_count"],
            require_user_verification=False,
        )
    except Exception as exc:
        raise _errors.AppError("INVALID_CREDENTIAL", str(exc), 401) from exc

    await _repo.mark_challenge_consumed(conn, challenge_id)
    await _repo.update_sign_count(conn, stored["id"], verified.new_sign_count)

    user = await _users_repo.get_by_id(conn, stored["user_id"])
    if user is None:
        raise _errors.AppError("USER_NOT_FOUND", "User not found.", 404)

    session_token, session = await _sessions_service.mint_session(
        conn, vault_client=vault_client, user_id=stored["user_id"], org_id=org_id,
    )
    return session_token, user, session


# ─── Credential management ────────────────────────────────────────────────────

async def list_credentials(conn: Any, *, user_id: str) -> list[dict]:
    return await _repo.list_credentials(conn, user_id)


async def delete_credential(conn: Any, *, cred_id: str, user_id: str) -> None:
    existing = await _repo.get_credentials_for_user(conn, user_id)
    target = next((c for c in existing if c["id"] == cred_id), None)
    if target is None:
        raise _errors.AppError("NOT_FOUND", "Passkey not found.", 404)
    await _repo.delete_credential(conn, cred_id, user_id)

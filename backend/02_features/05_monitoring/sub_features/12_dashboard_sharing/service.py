"""Business logic for dashboard sharing.

Handles grants, tokens, view recording, brute-force protection, and audit emission.
"""

import hashlib
import time
from datetime import datetime, timedelta
from importlib import import_module
from typing import Any, Optional

import bcrypt

from .repository import (
    count_recent_passphrase_failures,
    create_internal_grant,
    create_public_token_grant,
    get_share,
    get_token_hash,
    get_token_metadata,
    increment_view_count,
    record_event,
    revoke_share as revoke_share_db,
    rotate_token,
    soft_delete_share,
    update_passphrase,
    update_share_expiry,
)
from .token import hash_token, mint

_vault = import_module("backend.02_features.02_vault.sub_features.01_secrets")

# Brute-force protection: auto-revoke after 5 failures in 10 minutes
PASSPHRASE_MAX_FAILURES = 5
PASSPHRASE_FAILURE_WINDOW_MINUTES = 10


async def create_internal_share(
    conn: Any,
    dashboard_id: str,
    org_id: str,
    granted_by_user_id: str,
    granted_to_user_id: str,
    expires_at: Optional[datetime],
) -> dict:
    """Create an internal user share grant."""
    share_id = await create_internal_grant(
        conn, dashboard_id, org_id, granted_by_user_id, granted_to_user_id, expires_at
    )

    # Record event
    payload = {
        "granted_to_user_id": granted_to_user_id,
        "expires_at": expires_at.isoformat() if expires_at else None,
    }
    await record_event(
        conn,
        share_id=share_id,
        kind_id=1,  # granted
        actor_user_id=granted_by_user_id,
        viewer_email=None,
        viewer_ip=None,
        viewer_ua=None,
        payload=payload,
    )

    share = await get_share(conn, share_id)
    return dict(share) if share else {}


async def create_public_share(
    conn: Any,
    dashboard_id: str,
    org_id: str,
    granted_by_user_id: str,
    expires_at: Optional[datetime],
    passphrase: Optional[str],
    recipient_email: Optional[str],
    vault_client: Optional[Any] = None,
) -> dict:
    """Create a public token share. Returns share with plaintext token."""
    # Resolve signing key
    key_version = 1
    if vault_client:
        try:
            secret = vault_client.get_secret("monitoring/dashboard_share/signing_key/1")
            secret_bytes = secret.get("secret_bytes", "")
            if isinstance(secret_bytes, str):
                import base64

                secret_bytes = base64.b64decode(secret_bytes)
        except Exception:
            # Fallback to a default key (test only; ops must seed vault)
            secret_bytes = b"test-secret-key-32-bytes-minimum"
    else:
        secret_bytes = b"test-secret-key-32-bytes-minimum"

    # Mint token
    exp = (
        (expires_at.timestamp() if expires_at else time.time() + 86400 * 7)
        if expires_at
        else time.time() + 86400 * 7
    )
    token = mint(dashboard_id, exp, key_version, secret_bytes)
    token_hash_val = hash_token(token)

    # Hash passphrase if provided
    passphrase_hash = None
    if passphrase:
        passphrase_hash = bcrypt.hashpw(passphrase.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Create share
    share_id = await create_public_token_grant(
        conn,
        dashboard_id,
        org_id,
        granted_by_user_id,
        expires_at,
        recipient_email,
        token_hash_val,
        key_version,
        passphrase_hash,
    )

    # Record token_minted event
    payload = {
        "recipient_email": recipient_email,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "has_passphrase": passphrase is not None,
    }
    await record_event(
        conn,
        share_id=share_id,
        kind_id=3,  # token_minted
        actor_user_id=granted_by_user_id,
        viewer_email=recipient_email,
        viewer_ip=None,
        viewer_ua=None,
        payload=payload,
    )

    share = await get_share(conn, share_id)
    result = dict(share) if share else {}
    result["token"] = token
    return result


async def record_view(
    conn: Any,
    share_id: str,
    viewer_ip: Optional[str],
    viewer_ua: Optional[str],
    viewer_email: Optional[str],
) -> None:
    """Record a view event and increment counter."""
    await increment_view_count(conn, share_id)
    await record_event(
        conn,
        share_id=share_id,
        kind_id=2,  # viewed
        actor_user_id=None,
        viewer_email=viewer_email,
        viewer_ip=viewer_ip,
        viewer_ua=viewer_ua,
        payload={"viewer_ip": viewer_ip},
    )


async def record_passphrase_failure(
    conn: Any,
    share_id: str,
    viewer_ip: str,
) -> bool:
    """Record a passphrase failure. Returns True if share should be auto-revoked."""
    # Record the failure event
    await record_event(
        conn,
        share_id=share_id,
        kind_id=7,  # passphrase_failed
        actor_user_id=None,
        viewer_email=None,
        viewer_ip=viewer_ip,
        viewer_ua=None,
        payload={"viewer_ip": viewer_ip},
    )

    # Check failure count
    failure_count = await count_recent_passphrase_failures(
        conn, share_id, viewer_ip, PASSPHRASE_FAILURE_WINDOW_MINUTES
    )

    # Auto-revoke if >= threshold
    if failure_count >= PASSPHRASE_MAX_FAILURES:
        await revoke_share_db(conn, share_id, revoked_by_user_id="system")
        await record_event(
            conn,
            share_id=share_id,
            kind_id=5,  # revoked
            actor_user_id=None,
            viewer_email=None,
            viewer_ip=viewer_ip,
            viewer_ua=None,
            payload={"reason": "brute_force_protection"},
        )
        return True

    return False


async def verify_passphrase(
    conn: Any, share_id: str, provided_passphrase: str
) -> bool:
    """Verify passphrase against hash."""
    token_meta = await get_token_metadata(conn, share_id)
    if not token_meta or not token_meta.get("passphrase_hash"):
        return False  # No passphrase set

    stored_hash = token_meta["passphrase_hash"]
    return bcrypt.checkpw(
        provided_passphrase.encode("utf-8"), stored_hash.encode("utf-8")
    )


async def revoke_share(
    conn: Any, share_id: str, revoked_by_user_id: str
) -> None:
    """Revoke a share."""
    await revoke_share_db(conn, share_id, revoked_by_user_id)

    # Record revoke event
    await record_event(
        conn,
        share_id=share_id,
        kind_id=5,  # revoked
        actor_user_id=revoked_by_user_id,
        viewer_email=None,
        viewer_ip=None,
        viewer_ua=None,
        payload={"reason": "user_revocation"},
    )


async def soft_delete(conn: Any, share_id: str) -> None:
    """Soft-delete a share."""
    await soft_delete_share(conn, share_id)


async def rotate_public_token(
    conn: Any,
    share_id: str,
    granted_by_user_id: str,
    vault_client: Optional[Any] = None,
) -> dict:
    """Rotate a public share token. Returns new token in share response."""
    # Resolve signing key
    key_version = 1
    if vault_client:
        try:
            secret = vault_client.get_secret("monitoring/dashboard_share/signing_key/1")
            secret_bytes = secret.get("secret_bytes", "")
            if isinstance(secret_bytes, str):
                import base64

                secret_bytes = base64.b64decode(secret_bytes)
        except Exception:
            secret_bytes = b"test-secret-key-32-bytes-minimum"
    else:
        secret_bytes = b"test-secret-key-32-bytes-minimum"

    # Get share info
    share = await get_share(conn, share_id)
    if not share:
        raise ValueError(f"Share {share_id} not found")

    # Mint new token
    dashboard_id = share["dashboard_id"]
    expires_at = share["expires_at"]
    exp = (
        expires_at.timestamp()
        if expires_at
        else time.time() + 86400 * 7
    )
    new_token = mint(dashboard_id, exp, key_version, secret_bytes)
    new_token_hash = hash_token(new_token)

    # Update DB
    await rotate_token(conn, share_id, new_token_hash, key_version)

    # Record event
    await record_event(
        conn,
        share_id=share_id,
        kind_id=4,  # token_rotated
        actor_user_id=granted_by_user_id,
        viewer_email=None,
        viewer_ip=None,
        viewer_ua=None,
        payload={"old_token_hash": share.get("token_hash")},
    )

    share_result = await get_share(conn, share_id)
    result = dict(share_result) if share_result else {}
    result["token"] = new_token
    return result


async def extend_expiry(
    conn: Any, share_id: str, expires_at: Optional[datetime]
) -> None:
    """Extend or clear share expiration."""
    await update_share_expiry(conn, share_id, expires_at)


async def set_passphrase(
    conn: Any, share_id: str, passphrase: Optional[str]
) -> None:
    """Set or clear share passphrase."""
    passphrase_hash = None
    if passphrase:
        passphrase_hash = bcrypt.hashpw(
            passphrase.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    await update_passphrase(conn, share_id, passphrase_hash)

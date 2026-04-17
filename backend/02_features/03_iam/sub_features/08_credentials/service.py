"""
iam.credentials — service layer.

Argon2id password hashing with a peppered secret pulled from vault key
auth.argon2.pepper. The pepper is appended to the cleartext before hashing so
that a database leak of password_hash rows is not enough to mount an offline
attack — an attacker must also exfiltrate the vault root key.

VerifyMismatch / VerificationError from argon2-cffi map to a single boolean
result; callers convert that to UnauthorizedError at the auth layer. We never
log or echo the cleartext anywhere — even on failure.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.08_credentials.repository"
)

_hasher = PasswordHasher()

_PEPPER_VAULT_KEY = "auth.argon2.pepper"


async def _peppered(value: str, vault_client: Any) -> str:
    pepper = await vault_client.get(_PEPPER_VAULT_KEY)
    return f"{value}:{pepper}"


async def hash_password(value: str, vault_client: Any) -> str:
    """Return the PHC-encoded argon2id hash of `value` peppered with the vault pepper."""
    if not value:
        raise ValueError("password must be non-empty")
    return _hasher.hash(await _peppered(value, vault_client))


async def set_password(
    conn: Any,
    *,
    vault_client: Any,
    user_id: str,
    value: str,
) -> None:
    """Hash + store a password for an existing user. Idempotent (upsert)."""
    password_hash = await hash_password(value, vault_client)
    await _repo.upsert_hash(conn, user_id=user_id, password_hash=password_hash)


async def verify_password(
    conn: Any,
    *,
    vault_client: Any,
    user_id: str,
    value: str,
) -> bool:
    """Return True iff `value` matches the stored hash. Constant-time."""
    stored = await _repo.get_hash(conn, user_id)
    if stored is None:
        # Burn a cycle to avoid user-enumeration via timing — hash a dummy.
        try:
            _hasher.verify(
                "$argon2id$v=19$m=65536,t=3,p=4$AAAAAAAAAAAAAAAAAAAAAA$"
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
                "x",
            )
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            pass
        return False
    try:
        _hasher.verify(stored, await _peppered(value, vault_client))
        return True
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


async def delete_password(conn: Any, user_id: str) -> bool:
    return await _repo.delete_hash(conn, user_id)


async def change_password(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    vault_client: Any,
    user_id: str,
    current_password: str,
    new_password: str,
    current_session_id: str | None = None,
) -> int:
    """Verify `current_password`, hash + upsert `new_password`, revoke OTHER live sessions.

    Returns the count of other sessions revoked so the caller can surface
    "N other devices have been signed out." The current session is preserved
    so the user isn't immediately logged out of the tab they just used.
    """
    ok = await verify_password(
        conn, vault_client=vault_client, user_id=user_id, value=current_password,
    )
    if not ok:
        raise _errors.UnauthorizedError("current password is incorrect")

    if current_password == new_password:
        raise _errors.ValidationError("new password must differ from current password")

    await set_password(
        conn, vault_client=vault_client, user_id=user_id, value=new_password,
    )

    # Revoke sibling sessions. The caller's session row stays valid so the
    # response flight can land + the browser can stay logged in.
    revoked_ids = await conn.fetch(
        'SELECT id FROM "03_iam"."16_fct_sessions" '
        'WHERE user_id = $1 '
        '  AND deleted_at IS NULL '
        '  AND revoked_at IS NULL '
        '  AND ($2::varchar IS NULL OR id != $2) ',
        user_id, current_session_id,
    )
    if revoked_ids:
        await conn.execute(
            'UPDATE "03_iam"."16_fct_sessions" '
            'SET revoked_at = CURRENT_TIMESTAMP, '
            '    updated_by = $1, '
            '    updated_at = CURRENT_TIMESTAMP '
            'WHERE user_id = $2 '
            '  AND deleted_at IS NULL '
            '  AND revoked_at IS NULL '
            '  AND ($3::varchar IS NULL OR id != $3)',
            user_id, user_id, current_session_id,
        )

    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {
            "event_key": "iam.credentials.changed",
            "outcome": "success",
            "metadata": {
                "user_id": user_id,
                "other_sessions_revoked": len(revoked_ids),
            },
        },
    )
    return len(revoked_ids)

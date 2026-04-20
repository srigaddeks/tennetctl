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

import datetime as dt
import logging
from importlib import import_module
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.08_credentials.repository"
)
_core_id: Any = import_module("backend.01_core.id")

_PW_HISTORY_DEPTH_DEFAULT = 5

_hasher = PasswordHasher()
logger = logging.getLogger("tennetctl.iam.credentials")

_PEPPER_VAULT_KEY = "auth.argon2.pepper"


async def _peppered(value: str, vault_client: Any) -> str:
    pepper = await vault_client.get(_PEPPER_VAULT_KEY)
    return f"{value}:{pepper}"


async def hash_password(value: str, vault_client: Any) -> str:
    """Return the PHC-encoded argon2id hash of `value` peppered with the vault pepper."""
    if not value:
        raise ValueError("password must be non-empty")
    return _hasher.hash(await _peppered(value, vault_client))


async def _check_password_history(conn: Any, *, vault_client: Any, user_id: str, value: str, depth: int) -> None:
    """Raise AppError if `value` matches any of the last `depth` stored hashes."""
    recent = await _repo.list_recent_hashes(conn, user_id, depth)
    peppered = await _peppered(value, vault_client)
    for stored_hash in recent:
        try:
            _hasher.verify(stored_hash, peppered)
            raise _errors.AppError("PASSWORD_REUSED", "Password was recently used. Choose a different one.", 400)
        except _errors.AppError:
            raise
        except Exception:
            continue  # mismatch or invalid hash — not a reuse


async def set_password(
    conn: Any,
    *,
    vault_client: Any,
    user_id: str,
    value: str,
    check_history: bool = False,
    history_depth: int = _PW_HISTORY_DEPTH_DEFAULT,
) -> None:
    """Hash + store a password for an existing user. Idempotent (upsert).

    When check_history=True, raises PASSWORD_REUSED if `value` matches any of
    the last `history_depth` stored hashes, then pushes the new hash into history.
    """
    if check_history:
        await _check_password_history(conn, vault_client=vault_client, user_id=user_id, value=value, depth=history_depth)
    password_hash = await hash_password(value, vault_client)
    await _repo.upsert_hash(conn, user_id=user_id, password_hash=password_hash)
    if check_history:
        await _repo.push_hash(conn, id=_core_id.uuid7(), user_id=user_id, hash=password_hash)
        await _repo.prune_beyond(conn, user_id=user_id, depth=history_depth)


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


# ── Account lockout (Plan 20-03) ──────────────────────────────────────────────

async def check_lockout(
    conn: Any, *, user_id: str
) -> tuple[dt.datetime | None, bool]:
    """Return (locked_until, was_expired_and_cleared).

    - locked_until is non-None when the account is currently locked.
    - was_expired_and_cleared is True when a lockout existed but had expired;
      callers should emit iam.lockout.cleared for audit trail.
    """
    until = await _repo.get_lockout_until(conn, user_id=user_id)
    if until is None:
        return None, False
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    if until <= now:
        # Lockout expired — clear it proactively.
        try:
            await _repo.clear_lockout(conn, user_id=user_id)
        except Exception:
            pass
        return None, True
    return until, False


async def record_failure_and_maybe_lock(
    pool: Any,
    *,
    email: str,
    user_id: str | None,
    source_ip: str | None,
    auth_policy: Any,
    org_id: str | None,
) -> bool:
    """Record a failed attempt using a fresh connection (outside caller's tx).
    If threshold is reached, lock the user. Returns True if the user was locked.
    """
    # Use pool directly so this insert survives even if the caller rolls back.
    # timeout=5s ensures we never block the signin path long-term if the pool
    # is momentarily saturated.
    try:
        async with pool.acquire(timeout=5) as fresh_conn:
            await _repo.record_failed_attempt(
                fresh_conn, email=email, user_id=user_id, source_ip=source_ip,
            )
            if user_id is None:
                return False
            lockout_policy = await auth_policy.lockout(org_id)
            count = await _repo.count_failed_in_window(
                fresh_conn, email=email, window_seconds=lockout_policy.window_seconds,
            )
            if count >= lockout_policy.threshold_failed_attempts:
                until = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) + dt.timedelta(
                    seconds=lockout_policy.duration_seconds
                )
                await _repo.set_lockout_until(fresh_conn, user_id=user_id, until_ts=until)
                return True
    except Exception:
        logger.exception("record_failure_and_maybe_lock error (best-effort, ignored)")
    return False


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
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> tuple[int, str | None, dict | None]:
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
        check_history=True,
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

    # Plan 38-02: rotate the caller's own session — the one kept alive above.
    # The old session_id predates the new auth state (different password); a
    # replayed cookie from a leaked pre-change trace must not remain valid.
    new_token: str | None = None
    new_session: dict | None = None
    if current_session_id:
        try:
            from importlib import import_module as _im
            _sessions = _im(
                "backend.02_features.03_iam.sub_features.09_sessions.service"
            )
            new_token, new_session = await _sessions.rotate_on_privilege_escalation(
                pool, conn, ctx,
                previous_session_id=current_session_id,
                user_id=user_id,
                vault_client=vault_client,
                org_id=org_id,
                workspace_id=workspace_id,
                reason="password_change",
            )
        except Exception:
            # Rotation failure shouldn't fail the password change itself —
            # caller still gets the old session (which the password-change
            # flow kept alive by design). The audit emit inside the helper
            # already handles its own try/except.
            new_token, new_session = None, None

    return len(revoked_ids), new_token, new_session

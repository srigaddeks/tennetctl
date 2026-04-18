"""iam.impersonation — service layer.

Rules:
- Only super-admins (system-level, is_superadmin flag or specific role) can impersonate.
- Cannot impersonate another admin.
- Cannot nest impersonation (impersonation session cannot start another).
- Impersonation sessions have a 30-minute absolute TTL.
- All sessions are tracked in 45_lnk_impersonations for dual-actor audit.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.23_impersonation.repository"
)
_users_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.repository"
)
_sessions_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.repository"
)

_AUDIT = "audit.events.emit"
_IMPERSONATION_TTL_MINUTES = 30


async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict) -> None:
    try:
        await _catalog.run_node(pool, _AUDIT, ctx, {"event_key": event_key, "outcome": "success", "metadata": metadata})
    except Exception:
        pass


async def _is_super_admin(conn: Any, user_id: str) -> bool:
    """Super-admin = user assigned any system-type role (role_type_id=1)."""
    row = await conn.fetchrow(
        '''SELECT 1 FROM "03_iam"."42_lnk_user_roles" ur
           JOIN "03_iam"."13_fct_roles" r ON r.id = ur.role_id
           WHERE ur.user_id = $1 AND r.role_type_id = 1 AND r.deleted_at IS NULL
           LIMIT 1''',
        user_id,
    )
    return row is not None


async def start_impersonation(
    pool: Any, conn: Any, ctx: Any, vault: Any, *,
    impersonator_user_id: str, target_user_id: str, org_id: str,
    current_session_id: str,
) -> tuple[str, dict]:
    """Start impersonation. Returns (session_token, impersonation_row)."""
    # Guard: caller must be super-admin
    if not await _is_super_admin(conn, impersonator_user_id):
        raise _errors.AppError("FORBIDDEN", "Only super-admins can impersonate users.", 403)

    # Guard: cannot impersonate yourself
    if impersonator_user_id == target_user_id:
        raise _errors.AppError("FORBIDDEN", "Cannot impersonate yourself.", 403)

    # Guard: target user must exist
    target = await _users_repo.get_by_id(conn, target_user_id)
    if target is None:
        raise _errors.NotFoundError(f"User {target_user_id!r} not found")

    # Guard: cannot impersonate a super-admin
    if await _is_super_admin(conn, target_user_id):
        raise _errors.AppError("FORBIDDEN", "Cannot impersonate a super-admin.", 403)

    # Guard: reject if calling session is itself already an impersonation
    existing_imp = await _repo.get_active_by_session_id(conn, session_id=current_session_id)
    if existing_imp is not None:
        raise _errors.AppError("CONFLICT", "Nested impersonation is not allowed.", 409)

    # Mint a 30-minute session for the target user
    _sessions_svc: Any = import_module(
        "backend.02_features.03_iam.sub_features.09_sessions.service"
    )
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=_IMPERSONATION_TTL_MINUTES)
    session_id = _core_id.uuid7()
    await _sessions_repo.insert_session(
        conn, id=session_id, user_id=target_user_id, org_id=org_id,
        workspace_id=None, expires_at=expires_at, created_by=impersonator_user_id,
    )
    signing_key = await _sessions_svc._signing_key_bytes(vault)  # noqa: SLF001
    token = _sessions_svc.make_token(session_id, signing_key)

    # Record in lnk table
    imp_row = await _repo.insert_impersonation(
        conn, id=_core_id.uuid7(), session_id=session_id,
        impersonator_user_id=impersonator_user_id,
        impersonated_user_id=target_user_id,
        org_id=org_id, created_by=impersonator_user_id,
    )

    await _emit(pool, ctx, event_key="iam.impersonation.started", metadata={
        "impersonator_user_id": impersonator_user_id,
        "impersonated_user_id": target_user_id,
        "org_id": org_id,
    })
    return token, {**imp_row, "expires_at": expires_at.isoformat(), "target": target}


async def end_impersonation(
    pool: Any, conn: Any, ctx: Any, *,
    current_session_id: str, impersonator_user_id: str,
) -> None:
    """End the impersonation tied to the current session."""
    imp = await _repo.get_active_by_session_id(conn, session_id=current_session_id)
    if imp is None:
        raise _errors.NotFoundError("No active impersonation found for this session.")

    await _repo.end_impersonation(conn, impersonation_id=imp["id"])
    # Revoke the impersonation session
    await conn.execute(
        'UPDATE "03_iam"."16_fct_sessions" SET revoked_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $1 AND revoked_at IS NULL',
        current_session_id,
    )
    await _emit(pool, ctx, event_key="iam.impersonation.ended", metadata={
        "impersonator_user_id": impersonator_user_id,
        "impersonated_user_id": imp["impersonated_user_id"],
    })


async def get_active_impersonation_status(conn: Any, *, session_id: str) -> dict:
    """Return impersonation status for the given session."""
    imp = await _repo.get_active_by_session_id(conn, session_id=session_id)
    if imp is None:
        return {"active": False}
    # Get session for expires_at
    session = await _sessions_repo.get_by_id(conn, imp["session_id"])
    target = await _users_repo.get_by_id(conn, imp["impersonated_user_id"])
    return {
        "active": True,
        "impersonation_id": imp["id"],
        "impersonated_user_id": imp["impersonated_user_id"],
        "impersonated_display_name": target.get("display_name") if target else None,
        "impersonated_email": target.get("email") if target else None,
        "session_expires_at": session["expires_at"].isoformat() if session else None,
    }

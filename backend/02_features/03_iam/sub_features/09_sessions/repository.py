"""
iam.sessions — asyncpg repository.

Reads through v_sessions (carries derived is_valid). Writes target the raw
fct_sessions table. Soft-delete via deleted_at; signout sets revoked_at + flips
the row to invalid via the v_sessions derived flag.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


async def insert_session(
    conn: Any,
    *,
    id: str,
    user_id: str,
    org_id: str | None,
    workspace_id: str | None,
    expires_at: datetime,
    created_by: str,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> None:
    # Truncate UA to the column width (512) to avoid insert failures.
    if user_agent and len(user_agent) > 512:
        user_agent = user_agent[:512]
    await conn.execute(
        'INSERT INTO "03_iam"."16_fct_sessions" '
        '(id, user_id, org_id, workspace_id, expires_at, created_by, updated_by, '
        ' user_agent, ip_address) '
        'VALUES ($1, $2, $3, $4, $5, $6, $6, $7, $8)',
        id, user_id, org_id, workspace_id, expires_at, created_by,
        user_agent, ip_address,
    )


async def get_by_id(conn: Any, session_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, user_id, org_id, workspace_id, expires_at, revoked_at, '
        '       is_active, is_test, deleted_at, is_valid, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_sessions" WHERE id = $1',
        session_id,
    )
    return dict(row) if row else None


async def revoke_session(conn: Any, *, session_id: str, updated_by: str) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."16_fct_sessions" '
        'SET revoked_at = CURRENT_TIMESTAMP, '
        '    updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 '
        '  AND deleted_at IS NULL '
        '  AND revoked_at IS NULL',
        updated_by, session_id,
    )
    return result.endswith(" 1")


async def list_by_user(
    conn: Any,
    *,
    user_id: str,
    limit: int,
    offset: int,
    only_valid: bool,
) -> tuple[list[dict], int]:
    where = ["user_id = $1", "deleted_at IS NULL"]
    params: list[Any] = [user_id]
    if only_valid:
        where.append("is_valid = true")
    where_sql = " AND ".join(where)

    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "03_iam"."v_sessions" WHERE {where_sql}',
        *params,
    )
    params_page = [*params, limit, offset]
    rows = await conn.fetch(
        f'SELECT id, user_id, org_id, workspace_id, expires_at, revoked_at, '
        f'       is_active, is_test, deleted_at, is_valid, '
        f'       user_agent, ip_address, last_activity_at, '
        f'       created_by, updated_by, created_at, updated_at '
        f'FROM "03_iam"."v_sessions" '
        f'WHERE {where_sql} '
        f'ORDER BY created_at DESC, id DESC '
        f'LIMIT ${len(params_page) - 1} OFFSET ${len(params_page)}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def extend_expires(
    conn: Any, *, session_id: str, new_expires_at, updated_by: str,
) -> bool:
    """Push expires_at to `new_expires_at` iff the session is still live + unrevoked."""
    result = await conn.execute(
        'UPDATE "03_iam"."16_fct_sessions" '
        'SET expires_at = $1, '
        '    updated_by = $2, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $3 '
        '  AND deleted_at IS NULL '
        '  AND revoked_at IS NULL '
        '  AND expires_at > CURRENT_TIMESTAMP',
        new_expires_at, updated_by, session_id,
    )
    return result.endswith(" 1")


# ── Plan 20-04: Session limits ─────────────────────────────────────────────────

async def bump_last_activity(conn: Any, *, session_id: str) -> None:
    """Update last_activity_at = now for an active session. Best-effort."""
    await conn.execute(
        'UPDATE "03_iam"."16_fct_sessions" '
        'SET last_activity_at = CURRENT_TIMESTAMP '
        'WHERE id = $1 AND deleted_at IS NULL AND revoked_at IS NULL',
        session_id,
    )


async def list_active_for_user(conn: Any, *, user_id: str) -> list[dict]:
    """Return all active (unrevoked, unexpired) sessions for a user, ordered by activity."""
    rows = await conn.fetch(
        'SELECT id, user_id, org_id, created_at, last_activity_at '
        'FROM "03_iam"."16_fct_sessions" '
        'WHERE user_id = $1 '
        '  AND deleted_at IS NULL '
        '  AND revoked_at IS NULL '
        '  AND expires_at > CURRENT_TIMESTAMP '
        'ORDER BY last_activity_at ASC, created_at ASC',
        user_id,
    )
    return [dict(r) for r in rows]


async def revoke_session_by_reason(
    conn: Any, *, session_id: str, updated_by: str, reason: str = "",
) -> bool:
    """Revoke a session. reason is passed to the caller for audit metadata."""
    result = await conn.execute(
        'UPDATE "03_iam"."16_fct_sessions" '
        'SET revoked_at = CURRENT_TIMESTAMP, '
        '    updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL AND revoked_at IS NULL',
        updated_by, session_id,
    )
    return result.endswith(" 1")


async def get_raw_by_id(conn: Any, session_id: str) -> dict | None:
    """Fetch the raw fct_sessions row including last_activity_at and created_at."""
    row = await conn.fetchrow(
        'SELECT id, user_id, org_id, workspace_id, expires_at, revoked_at, '
        '       last_activity_at, created_at, deleted_at, is_active '
        'FROM "03_iam"."16_fct_sessions" WHERE id = $1',
        session_id,
    )
    return dict(row) if row else None


async def revoke_all_for_user(
    conn: Any, *, user_id: str, updated_by: str,
) -> list[str]:
    """Revoke all active sessions for a user. Returns list of revoked session IDs."""
    rows = await conn.fetch(
        'UPDATE "03_iam"."16_fct_sessions" '
        'SET revoked_at = CURRENT_TIMESTAMP, '
        '    updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE user_id = $2 '
        '  AND deleted_at IS NULL '
        '  AND revoked_at IS NULL '
        '  AND expires_at > CURRENT_TIMESTAMP '
        'RETURNING id',
        updated_by, user_id,
    )
    return [r["id"] for r in rows]

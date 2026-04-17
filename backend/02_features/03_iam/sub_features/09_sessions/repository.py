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
) -> None:
    await conn.execute(
        'INSERT INTO "03_iam"."16_fct_sessions" '
        '(id, user_id, org_id, workspace_id, expires_at, created_by, updated_by) '
        'VALUES ($1, $2, $3, $4, $5, $6, $6)',
        id, user_id, org_id, workspace_id, expires_at, created_by,
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

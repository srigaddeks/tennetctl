"""iam.setup — asyncpg repository."""

from __future__ import annotations

from typing import Any


async def count_users(conn: Any) -> int:
    """Return the count of non-deleted users in fct_users."""
    row = await conn.fetchrow(
        'SELECT COUNT(*) AS cnt FROM "03_iam"."12_fct_users" WHERE deleted_at IS NULL',
    )
    return int(row["cnt"]) if row else 0


async def get_role_by_code(conn: Any, code: str) -> dict | None:
    """Return a role by its code (global scope only)."""
    row = await conn.fetchrow(
        'SELECT id, code, label FROM "03_iam"."v_roles" '
        'WHERE code = $1 AND org_id IS NULL AND deleted_at IS NULL LIMIT 1',
        code,
    )
    return dict(row) if row else None


async def assign_global_role(
    conn: Any,
    *,
    lnk_id: str,
    user_id: str,
    role_id: str,
    created_by: str,
) -> None:
    """Insert a global lnk_user_roles row (user ↔ system role)."""
    await conn.execute(
        '''
        INSERT INTO "03_iam"."42_lnk_user_roles"
            (id, user_id, role_id, org_id, created_by, created_at)
        VALUES ($1, $2, $3, 'system', $4, CURRENT_TIMESTAMP)
        ON CONFLICT DO NOTHING
        ''',
        lnk_id, user_id, role_id, created_by,
    )

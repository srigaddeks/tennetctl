"""featureflags.permissions — asyncpg repository.

Reads v_role_flag_permissions. Writes lnk_role_flag_permissions.
Also provides shared `effective_permission_for_user_on_flag` used by other sub-features.
"""

from __future__ import annotations

from typing import Any


async def get_permission_id(conn: Any, code: str) -> int | None:
    return await conn.fetchval(
        'SELECT id FROM "09_featureflags"."04_dim_flag_permissions" WHERE code = $1',
        code,
    )


async def get_by_id(conn: Any, id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, role_id, flag_id, permission, permission_rank, created_by, created_at '
        'FROM "09_featureflags"."v_role_flag_permissions" WHERE id = $1',
        id,
    )
    return dict(row) if row else None


async def get_by_triple(
    conn: Any, *, role_id: str, flag_id: str, permission_id: int,
) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, role_id, flag_id, permission, permission_rank, created_by, created_at '
        'FROM "09_featureflags"."v_role_flag_permissions" '
        'WHERE role_id = $1 AND flag_id = $2 AND id IN ('
        '  SELECT id FROM "09_featureflags"."40_lnk_role_flag_permissions" '
        '  WHERE role_id = $1 AND flag_id = $2 AND permission_id = $3'
        ')',
        role_id, flag_id, permission_id,
    )
    return dict(row) if row else None


async def list_grants(
    conn: Any,
    *,
    limit: int,
    offset: int,
    role_id: str | None = None,
    flag_id: str | None = None,
    permission: str | None = None,
) -> tuple[list[dict], int]:
    where: list[str] = []
    params: list[Any] = []
    if role_id is not None:
        params.append(role_id)
        where.append(f"role_id = ${len(params)}")
    if flag_id is not None:
        params.append(flag_id)
        where.append(f"flag_id = ${len(params)}")
    if permission is not None:
        params.append(permission)
        where.append(f"permission = ${len(params)}")
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "09_featureflags"."v_role_flag_permissions" {where_sql}',
        *params,
    )
    params_page = [*params, limit, offset]
    l_idx, o_idx = len(params_page) - 1, len(params_page)
    rows = await conn.fetch(
        f'SELECT id, role_id, flag_id, permission, permission_rank, created_by, created_at '
        f'FROM "09_featureflags"."v_role_flag_permissions" '
        f'{where_sql} '
        f'ORDER BY flag_id, permission_rank DESC '
        f'LIMIT ${l_idx} OFFSET ${o_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def insert_grant(
    conn: Any,
    *,
    id: str,
    role_id: str,
    flag_id: str,
    permission_id: int,
    created_by: str,
) -> None:
    await conn.execute(
        'INSERT INTO "09_featureflags"."40_lnk_role_flag_permissions" '
        '  (id, role_id, flag_id, permission_id, created_by) '
        'VALUES ($1, $2, $3, $4, $5)',
        id, role_id, flag_id, permission_id, created_by,
    )


async def delete_grant(conn: Any, id: str) -> bool:
    result = await conn.execute(
        'DELETE FROM "09_featureflags"."40_lnk_role_flag_permissions" WHERE id = $1',
        id,
    )
    return result.endswith(" 1")


async def max_rank_for_user_on_flag(
    conn: Any, *, user_id: str, flag_id: str,
) -> int:
    """
    Given a user + flag, return the highest permission rank the user has on the
    flag via their assigned roles. Returns 0 if no permission.

    Joins: user → lnk_user_roles → fct_roles → lnk_role_flag_permissions.
    """
    row = await conn.fetchrow(
        """
        SELECT COALESCE(MAX(fp.rank), 0) AS max_rank
        FROM "03_iam"."42_lnk_user_roles" ur
        JOIN "09_featureflags"."40_lnk_role_flag_permissions" rfp
            ON rfp.role_id = ur.role_id
        JOIN "09_featureflags"."04_dim_flag_permissions" fp
            ON fp.id = rfp.permission_id
        WHERE ur.user_id = $1 AND rfp.flag_id = $2
        """,
        user_id, flag_id,
    )
    return int(row["max_rank"]) if row else 0


async def user_has_admin_all_scope(conn: Any, user_id: str) -> bool:
    """True if any of the user's roles holds scope code flags:admin:all."""
    return bool(
        await conn.fetchval(
            """
            SELECT 1 FROM "03_iam"."42_lnk_user_roles" ur
            JOIN "03_iam"."44_lnk_role_scopes" rs ON rs.role_id = ur.role_id
            JOIN "03_iam"."03_dim_scopes" s ON s.id = rs.scope_id
            WHERE ur.user_id = $1 AND s.code = 'flags:admin:all'
            LIMIT 1
            """,
            user_id,
        )
    )

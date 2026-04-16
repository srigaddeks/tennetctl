"""
iam.users — asyncpg repository.

Reads through `v_users` (flat shape; account_type resolved from dim; email /
display_name / avatar_url pivoted from dtl_attrs). Writes target fct_users +
dtl_attrs (entity_type_id=3).
"""

from __future__ import annotations

from typing import Any

_USER_ENTITY_TYPE_ID = 3


async def _attr_def_id(conn: Any, attr_code: str) -> int:
    row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."20_dtl_attr_defs" '
        'WHERE entity_type_id = $1 AND code = $2',
        _USER_ENTITY_TYPE_ID,
        attr_code,
    )
    if row is None:
        raise RuntimeError(
            f"attr_def missing: (entity_type_id=3, code={attr_code!r})."
        )
    return int(row["id"])


async def get_account_type_id(conn: Any, code: str) -> int | None:
    return await conn.fetchval(
        'SELECT id FROM "03_iam"."02_dim_account_types" WHERE code = $1',
        code,
    )


async def get_by_id(conn: Any, user_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, account_type, email, display_name, avatar_url, '
        '       is_active, is_test, created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_users" '
        'WHERE id = $1 AND deleted_at IS NULL',
        user_id,
    )
    return dict(row) if row else None


async def list_users(
    conn: Any,
    *,
    limit: int,
    offset: int,
    account_type: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    where = ["deleted_at IS NULL"]
    params: list[Any] = []
    if account_type is not None:
        params.append(account_type)
        where.append(f"account_type = ${len(params)}")
    if is_active is not None:
        params.append(is_active)
        where.append(f"is_active = ${len(params)}")
    where_sql = " AND ".join(where)

    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "03_iam"."v_users" WHERE {where_sql}',
        *params,
    )

    params_page = [*params, limit, offset]
    limit_idx = len(params_page) - 1
    offset_idx = len(params_page)
    rows = await conn.fetch(
        f'SELECT id, account_type, email, display_name, avatar_url, '
        f'       is_active, is_test, created_by, updated_by, created_at, updated_at '
        f'FROM "03_iam"."v_users" '
        f'WHERE {where_sql} '
        f'ORDER BY created_at DESC, id DESC '
        f'LIMIT ${limit_idx} OFFSET ${offset_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def insert_user(
    conn: Any,
    *,
    id: str,
    account_type_id: int,
    created_by: str,
) -> None:
    await conn.execute(
        'INSERT INTO "03_iam"."12_fct_users" '
        '    (id, account_type_id, created_by, updated_by) '
        'VALUES ($1, $2, $3, $3)',
        id,
        account_type_id,
        created_by,
    )


async def set_attr(
    conn: Any,
    *,
    user_id: str,
    attr_code: str,
    value: str,
    attr_row_id: str,
) -> None:
    """Upsert a user EAV attribute (email / display_name / avatar_url)."""
    def_id = await _attr_def_id(conn, attr_code)
    await conn.execute(
        'INSERT INTO "03_iam"."21_dtl_attrs" '
        '    (id, entity_type_id, entity_id, attr_def_id, key_text) '
        'VALUES ($1, $2, $3, $4, $5) '
        'ON CONFLICT (entity_type_id, entity_id, attr_def_id) '
        '    DO UPDATE SET key_text = EXCLUDED.key_text',
        attr_row_id,
        _USER_ENTITY_TYPE_ID,
        user_id,
        def_id,
        value,
    )


async def update_active(
    conn: Any,
    *,
    id: str,
    is_active: bool,
    updated_by: str,
) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."12_fct_users" '
        'SET is_active = $1, updated_by = $2, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $3 AND deleted_at IS NULL',
        is_active,
        updated_by,
        id,
    )
    return result.endswith(" 1")


async def touch_user(
    conn: Any,
    *,
    id: str,
    updated_by: str,
) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."12_fct_users" '
        'SET updated_by = $1, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by,
        id,
    )
    return result.endswith(" 1")


async def soft_delete_user(
    conn: Any,
    *,
    id: str,
    updated_by: str,
) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."12_fct_users" '
        'SET deleted_at = CURRENT_TIMESTAMP, '
        '    updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by,
        id,
    )
    return result.endswith(" 1")

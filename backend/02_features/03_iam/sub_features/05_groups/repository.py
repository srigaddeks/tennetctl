"""iam.groups — asyncpg repository. entity_type_id=5."""

from __future__ import annotations

from typing import Any

_GROUP_ENTITY_TYPE_ID = 5


async def _attr_def_id(conn: Any, code: str) -> int:
    row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."20_dtl_attr_defs" '
        'WHERE entity_type_id = $1 AND code = $2',
        _GROUP_ENTITY_TYPE_ID, code,
    )
    if row is None:
        raise RuntimeError(f"attr_def missing: (entity_type=5, code={code!r})")
    return int(row["id"])


async def get_by_id(conn: Any, group_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, org_id, application_id, code, label, description, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_groups" '
        'WHERE id = $1 AND deleted_at IS NULL',
        group_id,
    )
    return dict(row) if row else None


async def get_by_org_code(conn: Any, org_id: str, code: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, org_id, application_id, code, label, description, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_groups" '
        'WHERE org_id = $1 AND code = $2 AND deleted_at IS NULL',
        org_id, code,
    )
    return dict(row) if row else None


async def list_groups(
    conn: Any, *,
    limit: int, offset: int,
    org_id: str | None = None,
    is_active: bool | None = None,
    application_id: str | None = None,
) -> tuple[list[dict], int]:
    where = ["deleted_at IS NULL"]
    params: list[Any] = []
    if org_id is not None:
        params.append(org_id)
        where.append(f"org_id = ${len(params)}")
    if is_active is not None:
        params.append(is_active)
        where.append(f"is_active = ${len(params)}")
    if application_id is not None:
        params.append(application_id)
        where.append(f"application_id = ${len(params)}")
    where_sql = " AND ".join(where)

    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "03_iam"."v_groups" WHERE {where_sql}',
        *params,
    )
    params_page = [*params, limit, offset]
    limit_idx = len(params_page) - 1
    offset_idx = len(params_page)
    rows = await conn.fetch(
        f'SELECT id, org_id, application_id, code, label, description, is_active, is_test, '
        f'       created_by, updated_by, created_at, updated_at '
        f'FROM "03_iam"."v_groups" WHERE {where_sql} '
        f'ORDER BY created_at DESC, id DESC '
        f'LIMIT ${limit_idx} OFFSET ${offset_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def insert_group(
    conn: Any, *, id: str, org_id: str, created_by: str,
    application_id: str | None = None,
) -> None:
    await conn.execute(
        'INSERT INTO "03_iam"."14_fct_groups" '
        '    (id, org_id, application_id, created_by, updated_by) '
        'VALUES ($1, $2, $3, $4, $4)',
        id, org_id, application_id, created_by,
    )


async def set_attr(
    conn: Any, *,
    group_id: str, attr_code: str, value: str, attr_row_id: str,
) -> None:
    def_id = await _attr_def_id(conn, attr_code)
    await conn.execute(
        'INSERT INTO "03_iam"."21_dtl_attrs" '
        '    (id, entity_type_id, entity_id, attr_def_id, key_text) '
        'VALUES ($1, $2, $3, $4, $5) '
        'ON CONFLICT (entity_type_id, entity_id, attr_def_id) '
        '    DO UPDATE SET key_text = EXCLUDED.key_text',
        attr_row_id, _GROUP_ENTITY_TYPE_ID, group_id, def_id, value,
    )


async def update_active(conn: Any, *, id: str, is_active: bool, updated_by: str) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."14_fct_groups" '
        'SET is_active = $1, updated_by = $2, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $3 AND deleted_at IS NULL',
        is_active, updated_by, id,
    )
    return result.endswith(" 1")


async def touch_group(conn: Any, *, id: str, updated_by: str) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."14_fct_groups" '
        'SET updated_by = $1, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by, id,
    )
    return result.endswith(" 1")


async def soft_delete_group(conn: Any, *, id: str, updated_by: str) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."14_fct_groups" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by, id,
    )
    return result.endswith(" 1")


# ── Membership (lnk_user_groups) ─────────────────────────────────────────


async def list_members(conn: Any, *, group_id: str) -> list[dict]:
    """Active members of a group, joined with user account_type for context."""
    rows = await conn.fetch(
        '''
        SELECT
            lug.id            AS membership_id,
            lug.user_id,
            lug.group_id,
            lug.org_id,
            lug.created_at,
            lug.created_by,
            u.account_type_id,
            t.code            AS account_type_code,
            COALESCE(uemail.key_text, '') AS user_email,
            COALESCE(uname.key_text, '')  AS user_display_name
        FROM "03_iam"."43_lnk_user_groups" lug
        JOIN "03_iam"."12_fct_users" u ON u.id = lug.user_id AND u.deleted_at IS NULL
        JOIN "03_iam"."02_dim_account_types" t ON t.id = u.account_type_id
        LEFT JOIN "03_iam"."21_dtl_attrs" uemail
               ON uemail.entity_id = u.id
              AND uemail.attr_def_id = (SELECT id FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id = 3 AND code = 'email'        LIMIT 1)
        LEFT JOIN "03_iam"."21_dtl_attrs" uname
               ON uname.entity_id = u.id
              AND uname.attr_def_id = (SELECT id FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id = 3 AND code = 'display_name' LIMIT 1)
        WHERE lug.group_id = $1
        ORDER BY lug.created_at ASC
        ''',
        group_id,
    )
    return [dict(r) for r in rows]


async def add_member(
    conn: Any,
    *,
    id: str,
    user_id: str,
    group_id: str,
    org_id: str,
    created_by: str,
) -> dict:
    row = await conn.fetchrow(
        'INSERT INTO "03_iam"."43_lnk_user_groups" '
        '    (id, user_id, group_id, org_id, created_by, created_at) '
        'VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP) '
        'ON CONFLICT (user_id, group_id, org_id) DO UPDATE '
        '    SET created_at = "03_iam"."43_lnk_user_groups".created_at '
        'RETURNING id, user_id, group_id, org_id, created_at',
        id, user_id, group_id, org_id, created_by,
    )
    return dict(row)


async def remove_member(
    conn: Any, *, user_id: str, group_id: str, org_id: str,
) -> bool:
    result = await conn.execute(
        'DELETE FROM "03_iam"."43_lnk_user_groups" '
        'WHERE user_id = $1 AND group_id = $2 AND org_id = $3',
        user_id, group_id, org_id,
    )
    return result.endswith(" 1")

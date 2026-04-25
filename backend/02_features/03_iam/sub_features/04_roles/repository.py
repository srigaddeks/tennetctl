"""iam.roles — asyncpg repository. entity_type_id=4."""

from __future__ import annotations

from typing import Any

_ROLE_ENTITY_TYPE_ID = 4


async def _attr_def_id(conn: Any, code: str) -> int:
    row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."20_dtl_attr_defs" '
        'WHERE entity_type_id = $1 AND code = $2',
        _ROLE_ENTITY_TYPE_ID, code,
    )
    if row is None:
        raise RuntimeError(f"attr_def missing: (entity_type=4, code={code!r})")
    return int(row["id"])


async def get_role_type_id(conn: Any, code: str) -> int | None:
    return await conn.fetchval(
        'SELECT id FROM "03_iam"."04_dim_role_types" WHERE code = $1',
        code,
    )


async def get_by_id(conn: Any, role_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, org_id, application_id, role_type, code, label, description, '
        '       is_active, is_test, created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_roles" '
        'WHERE id = $1 AND deleted_at IS NULL',
        role_id,
    )
    return dict(row) if row else None


async def get_by_org_code(conn: Any, org_id: str | None, code: str) -> dict | None:
    # IS NOT DISTINCT FROM handles NULL equality for global roles.
    row = await conn.fetchrow(
        'SELECT id, org_id, application_id, role_type, code, label, description, '
        '       is_active, is_test, created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_roles" '
        'WHERE org_id IS NOT DISTINCT FROM $1 AND code = $2 AND deleted_at IS NULL',
        org_id, code,
    )
    return dict(row) if row else None


async def list_roles(
    conn: Any,
    *,
    limit: int,
    offset: int,
    org_id: str | None = None,
    role_type: str | None = None,
    is_active: bool | None = None,
    application_id: str | None = None,
) -> tuple[list[dict], int]:
    where = ["deleted_at IS NULL"]
    params: list[Any] = []
    if org_id is not None:
        params.append(org_id)
        where.append(f"org_id = ${len(params)}")
    if role_type is not None:
        params.append(role_type)
        where.append(f"role_type = ${len(params)}")
    if is_active is not None:
        params.append(is_active)
        where.append(f"is_active = ${len(params)}")
    if application_id is not None:
        params.append(application_id)
        where.append(f"application_id = ${len(params)}")
    where_sql = " AND ".join(where)

    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "03_iam"."v_roles" WHERE {where_sql}',
        *params,
    )
    params_page = [*params, limit, offset]
    limit_idx = len(params_page) - 1
    offset_idx = len(params_page)
    rows = await conn.fetch(
        f'SELECT id, org_id, application_id, role_type, code, label, description, '
        f'       is_active, is_test, created_by, updated_by, created_at, updated_at '
        f'FROM "03_iam"."v_roles" WHERE {where_sql} '
        f'ORDER BY created_at DESC, id DESC '
        f'LIMIT ${limit_idx} OFFSET ${offset_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def insert_role(
    conn: Any,
    *,
    id: str,
    org_id: str | None,
    role_type_id: int,
    created_by: str,
    application_id: str | None = None,
) -> None:
    await conn.execute(
        'INSERT INTO "03_iam"."13_fct_roles" '
        '    (id, org_id, application_id, role_type_id, created_by, updated_by) '
        'VALUES ($1, $2, $3, $4, $5, $5)',
        id, org_id, application_id, role_type_id, created_by,
    )


async def set_attr(
    conn: Any,
    *,
    role_id: str,
    attr_code: str,
    value: str,
    attr_row_id: str,
) -> None:
    def_id = await _attr_def_id(conn, attr_code)
    await conn.execute(
        'INSERT INTO "03_iam"."21_dtl_attrs" '
        '    (id, entity_type_id, entity_id, attr_def_id, key_text) '
        'VALUES ($1, $2, $3, $4, $5) '
        'ON CONFLICT (entity_type_id, entity_id, attr_def_id) '
        '    DO UPDATE SET key_text = EXCLUDED.key_text',
        attr_row_id, _ROLE_ENTITY_TYPE_ID, role_id, def_id, value,
    )


async def update_active(conn: Any, *, id: str, is_active: bool, updated_by: str) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."13_fct_roles" '
        'SET is_active = $1, updated_by = $2, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $3 AND deleted_at IS NULL',
        is_active, updated_by, id,
    )
    return result.endswith(" 1")


async def touch_role(conn: Any, *, id: str, updated_by: str) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."13_fct_roles" '
        'SET updated_by = $1, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by, id,
    )
    return result.endswith(" 1")


async def assign_role(
    conn: Any,
    *,
    id: str,
    user_id: str,
    role_id: str,
    org_id: str,
    created_by: str,
    expires_at: Any = None,
) -> dict:
    row = await conn.fetchrow(
        'INSERT INTO "03_iam"."42_lnk_user_roles" '
        '    (id, user_id, role_id, org_id, created_by, expires_at, created_at) '
        'VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP) '
        'ON CONFLICT (user_id, role_id, org_id) DO UPDATE '
        '    SET expires_at = EXCLUDED.expires_at, revoked_at = NULL '
        'RETURNING id, user_id, role_id, org_id, expires_at, revoked_at, created_at',
        id, user_id, role_id, org_id, created_by, expires_at,
    )
    return dict(row)


async def revoke_role(
    conn: Any,
    *,
    user_id: str,
    role_id: str,
    org_id: str,
) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."42_lnk_user_roles" '
        'SET revoked_at = CURRENT_TIMESTAMP '
        'WHERE user_id = $1 AND role_id = $2 AND org_id = $3 AND revoked_at IS NULL',
        user_id, role_id, org_id,
    )
    return result.endswith(" 1")


async def list_roles_for_user(conn: Any, *, user_id: str) -> list[dict]:
    """Active role assignments for a user, joined with role label/code."""
    rows = await conn.fetch(
        '''
        SELECT
            lur.id            AS assignment_id,
            lur.user_id,
            lur.role_id,
            lur.org_id,
            lur.expires_at,
            lur.revoked_at,
            lur.created_at,
            r.application_id,
            r.is_active,
            COALESCE(rcode.key_text, '')    AS role_code,
            COALESCE(rlabel.key_text, '')   AS role_label,
            COALESCE(rdesc.key_text, '')    AS role_description
        FROM "03_iam"."42_lnk_user_roles" lur
        JOIN "03_iam"."13_fct_roles" r ON r.id = lur.role_id AND r.deleted_at IS NULL
        LEFT JOIN "03_iam"."21_dtl_attrs" rcode  ON rcode.entity_id = r.id  AND rcode.attr_def_id  = (SELECT id FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id = 4 AND code = 'code'        LIMIT 1)
        LEFT JOIN "03_iam"."21_dtl_attrs" rlabel ON rlabel.entity_id = r.id AND rlabel.attr_def_id = (SELECT id FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id = 4 AND code = 'label'       LIMIT 1)
        LEFT JOIN "03_iam"."21_dtl_attrs" rdesc  ON rdesc.entity_id = r.id  AND rdesc.attr_def_id  = (SELECT id FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id = 4 AND code = 'description' LIMIT 1)
        WHERE lur.user_id = $1
          AND lur.revoked_at IS NULL
          AND (lur.expires_at IS NULL OR lur.expires_at > CURRENT_TIMESTAMP)
        ORDER BY lur.created_at DESC
        ''',
        user_id,
    )
    return [dict(r) for r in rows]


async def expire_due(conn: Any) -> list[dict]:
    """Mark all expired, non-revoked assignments as revoked. Returns revoked rows."""
    rows = await conn.fetch(
        'UPDATE "03_iam"."42_lnk_user_roles" '
        'SET revoked_at = CURRENT_TIMESTAMP '
        'WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP '
        '  AND revoked_at IS NULL '
        'RETURNING id, user_id, role_id, org_id, expires_at',
    )
    return [dict(r) for r in rows]


async def soft_delete_role(conn: Any, *, id: str, updated_by: str) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."13_fct_roles" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by, id,
    )
    return result.endswith(" 1")

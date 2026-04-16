"""iam.applications — asyncpg repository. entity_type_id=6."""

from __future__ import annotations

from typing import Any

_APPLICATION_ENTITY_TYPE_ID = 6


async def _attr_def_id(conn: Any, code: str) -> int:
    row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."20_dtl_attr_defs" '
        'WHERE entity_type_id = $1 AND code = $2',
        _APPLICATION_ENTITY_TYPE_ID, code,
    )
    if row is None:
        raise RuntimeError(f"attr_def missing: (entity_type=6, code={code!r})")
    return int(row["id"])


async def get_by_id(conn: Any, application_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, org_id, code, label, description, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_applications" '
        'WHERE id = $1 AND deleted_at IS NULL',
        application_id,
    )
    return dict(row) if row else None


async def get_by_org_code(conn: Any, org_id: str, code: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, org_id, code, label, description, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_applications" '
        'WHERE org_id = $1 AND code = $2 AND deleted_at IS NULL',
        org_id, code,
    )
    return dict(row) if row else None


async def list_applications(
    conn: Any, *,
    limit: int, offset: int,
    org_id: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    where = ["deleted_at IS NULL"]
    params: list[Any] = []
    if org_id is not None:
        params.append(org_id)
        where.append(f"org_id = ${len(params)}")
    if is_active is not None:
        params.append(is_active)
        where.append(f"is_active = ${len(params)}")
    where_sql = " AND ".join(where)

    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "03_iam"."v_applications" WHERE {where_sql}',
        *params,
    )
    params_page = [*params, limit, offset]
    limit_idx = len(params_page) - 1
    offset_idx = len(params_page)
    rows = await conn.fetch(
        f'SELECT id, org_id, code, label, description, is_active, is_test, '
        f'       created_by, updated_by, created_at, updated_at '
        f'FROM "03_iam"."v_applications" WHERE {where_sql} '
        f'ORDER BY created_at DESC, id DESC '
        f'LIMIT ${limit_idx} OFFSET ${offset_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def insert_application(conn: Any, *, id: str, org_id: str, created_by: str) -> None:
    await conn.execute(
        'INSERT INTO "03_iam"."15_fct_applications" '
        '    (id, org_id, created_by, updated_by) '
        'VALUES ($1, $2, $3, $3)',
        id, org_id, created_by,
    )


async def set_attr(
    conn: Any, *,
    application_id: str, attr_code: str, value: str, attr_row_id: str,
) -> None:
    def_id = await _attr_def_id(conn, attr_code)
    await conn.execute(
        'INSERT INTO "03_iam"."21_dtl_attrs" '
        '    (id, entity_type_id, entity_id, attr_def_id, key_text) '
        'VALUES ($1, $2, $3, $4, $5) '
        'ON CONFLICT (entity_type_id, entity_id, attr_def_id) '
        '    DO UPDATE SET key_text = EXCLUDED.key_text',
        attr_row_id, _APPLICATION_ENTITY_TYPE_ID, application_id, def_id, value,
    )


async def update_active(conn: Any, *, id: str, is_active: bool, updated_by: str) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."15_fct_applications" '
        'SET is_active = $1, updated_by = $2, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $3 AND deleted_at IS NULL',
        is_active, updated_by, id,
    )
    return result.endswith(" 1")


async def touch_application(conn: Any, *, id: str, updated_by: str) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."15_fct_applications" '
        'SET updated_by = $1, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by, id,
    )
    return result.endswith(" 1")


async def soft_delete_application(conn: Any, *, id: str, updated_by: str) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."15_fct_applications" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by, id,
    )
    return result.endswith(" 1")

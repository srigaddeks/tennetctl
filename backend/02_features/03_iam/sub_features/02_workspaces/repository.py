"""
iam.workspaces — asyncpg repository.

Reads through "03_iam"."v_workspaces" (flat shape with pivoted display_name).
Writes hit raw fct_workspaces + dtl_attrs. entity_type_id=2 is workspace.
"""

from __future__ import annotations

from typing import Any

_WORKSPACE_ENTITY_TYPE_ID = 2  # dim_entity_types row for "workspace"


async def _get_display_name_attr_def_id(conn: Any) -> int:
    row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."20_dtl_attr_defs" '
        'WHERE entity_type_id = $1 AND code = $2',
        _WORKSPACE_ENTITY_TYPE_ID,
        "display_name",
    )
    if row is None:
        raise RuntimeError(
            "attr_def missing: (entity_type_id=2, code='display_name'). "
            "Re-run IAM bootstrap migrations."
        )
    return int(row["id"])


async def get_by_id(conn: Any, workspace_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, org_id, slug, display_name, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_workspaces" '
        'WHERE id = $1 AND deleted_at IS NULL',
        workspace_id,
    )
    return dict(row) if row else None


async def get_many(conn: Any, ids: list[str]) -> dict[str, dict]:
    """Bulk-read by id — one query via ANY($1). Returns {id: row} for existing non-deleted rows; missing/deleted ids omitted (Plan 39-02)."""
    if not ids:
        return {}
    rows = await conn.fetch(
        'SELECT id, org_id, slug, display_name, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_workspaces" '
        'WHERE id = ANY($1::varchar[]) AND deleted_at IS NULL',
        ids,
    )
    return {r["id"]: dict(r) for r in rows}


async def get_by_org_slug(conn: Any, org_id: str, slug: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, org_id, slug, display_name, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_workspaces" '
        'WHERE org_id = $1 AND slug = $2 AND deleted_at IS NULL',
        org_id,
        slug,
    )
    return dict(row) if row else None


async def list_workspaces(
    conn: Any,
    *,
    limit: int,
    offset: int,
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
        f'SELECT COUNT(*) FROM "03_iam"."v_workspaces" WHERE {where_sql}',
        *params,
    )

    params_page = [*params, limit, offset]
    limit_idx = len(params_page) - 1
    offset_idx = len(params_page)
    rows = await conn.fetch(
        f'SELECT id, org_id, slug, display_name, is_active, is_test, '
        f'       created_by, updated_by, created_at, updated_at '
        f'FROM "03_iam"."v_workspaces" '
        f'WHERE {where_sql} '
        f'ORDER BY created_at DESC, id DESC '
        f'LIMIT ${limit_idx} OFFSET ${offset_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def insert_workspace(
    conn: Any,
    *,
    id: str,
    org_id: str,
    slug: str,
    created_by: str,
) -> None:
    await conn.execute(
        'INSERT INTO "03_iam"."11_fct_workspaces" '
        '    (id, org_id, slug, created_by, updated_by) '
        'VALUES ($1, $2, $3, $4, $4)',
        id,
        org_id,
        slug,
        created_by,
    )


async def update_workspace_slug(
    conn: Any,
    *,
    id: str,
    slug: str,
    updated_by: str,
) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."11_fct_workspaces" '
        'SET slug = $1, updated_by = $2, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $3 AND deleted_at IS NULL',
        slug,
        updated_by,
        id,
    )
    return result.endswith(" 1")


async def touch_workspace(
    conn: Any,
    *,
    id: str,
    updated_by: str,
) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."11_fct_workspaces" '
        'SET updated_by = $1, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by,
        id,
    )
    return result.endswith(" 1")


async def soft_delete_workspace(
    conn: Any,
    *,
    id: str,
    updated_by: str,
) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."11_fct_workspaces" '
        'SET deleted_at = CURRENT_TIMESTAMP, '
        '    updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by,
        id,
    )
    return result.endswith(" 1")


async def set_display_name(
    conn: Any,
    *,
    workspace_id: str,
    display_name: str,
    attr_row_id: str,
) -> None:
    attr_def_id = await _get_display_name_attr_def_id(conn)
    await conn.execute(
        'INSERT INTO "03_iam"."21_dtl_attrs" '
        '    (id, entity_type_id, entity_id, attr_def_id, key_text) '
        'VALUES ($1, $2, $3, $4, $5) '
        'ON CONFLICT (entity_type_id, entity_id, attr_def_id) '
        '    DO UPDATE SET key_text = EXCLUDED.key_text',
        attr_row_id,
        _WORKSPACE_ENTITY_TYPE_ID,
        workspace_id,
        attr_def_id,
        display_name,
    )

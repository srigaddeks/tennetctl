"""
iam.orgs — asyncpg repository.

Reads go through "03_iam"."v_orgs" (flat shape including pivoted display_name).
Writes hit raw fct_orgs + dtl_attrs tables. Connection is always passed in —
the repo never acquires from a pool. No business logic; callers (service) own
slug uniqueness + audit emission.
"""

from __future__ import annotations

from typing import Any

_ORG_ENTITY_TYPE_ID = 1  # dim_entity_types row for "org"


async def _get_display_name_attr_def_id(conn: Any) -> int:
    """Look up the attr_def_id for (entity_type=org, code=display_name)."""
    row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."20_dtl_attr_defs" '
        'WHERE entity_type_id = $1 AND code = $2',
        _ORG_ENTITY_TYPE_ID,
        "display_name",
    )
    if row is None:
        raise RuntimeError(
            "attr_def missing: (entity_type_id=1, code='display_name'). "
            "Re-run IAM bootstrap migrations."
        )
    return int(row["id"])


async def get_by_id(conn: Any, org_id: str) -> dict | None:
    """Return v_orgs row (excludes soft-deleted) or None."""
    row = await conn.fetchrow(
        'SELECT id, slug, display_name, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_orgs" '
        'WHERE id = $1 AND deleted_at IS NULL',
        org_id,
    )
    return dict(row) if row else None


async def get_by_slug(conn: Any, slug: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, slug, display_name, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "03_iam"."v_orgs" '
        'WHERE slug = $1 AND deleted_at IS NULL',
        slug,
    )
    return dict(row) if row else None


async def list_orgs(
    conn: Any,
    *,
    limit: int,
    offset: int,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    """
    Paginated list of orgs. Always excludes soft-deleted rows. Optional
    is_active filter for explicit active/inactive partitioning.
    """
    where = ["deleted_at IS NULL"]
    params: list[Any] = []
    if is_active is not None:
        params.append(is_active)
        where.append(f"is_active = ${len(params)}")
    where_sql = " AND ".join(where)

    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "03_iam"."v_orgs" WHERE {where_sql}',
        *params,
    )

    params_page = [*params, limit, offset]
    limit_idx = len(params_page) - 1
    offset_idx = len(params_page)
    rows = await conn.fetch(
        f'SELECT id, slug, display_name, is_active, is_test, '
        f'       created_by, updated_by, created_at, updated_at '
        f'FROM "03_iam"."v_orgs" '
        f'WHERE {where_sql} '
        f'ORDER BY created_at DESC, id DESC '
        f'LIMIT ${limit_idx} OFFSET ${offset_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def insert_org(
    conn: Any,
    *,
    id: str,
    slug: str,
    created_by: str,
) -> None:
    """Insert a new row into fct_orgs. Caller catches UniqueViolationError on slug collision."""
    await conn.execute(
        'INSERT INTO "03_iam"."10_fct_orgs" (id, slug, created_by, updated_by) '
        'VALUES ($1, $2, $3, $3)',
        id,
        slug,
        created_by,
    )


async def update_org_slug(
    conn: Any,
    *,
    id: str,
    slug: str,
    updated_by: str,
) -> bool:
    """Update slug. Returns True if one row updated, False if not found / soft-deleted."""
    result = await conn.execute(
        'UPDATE "03_iam"."10_fct_orgs" '
        'SET slug = $1, updated_by = $2, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $3 AND deleted_at IS NULL',
        slug,
        updated_by,
        id,
    )
    return result.endswith(" 1")


async def touch_org(
    conn: Any,
    *,
    id: str,
    updated_by: str,
) -> bool:
    """Bump updated_at / updated_by without other column changes (e.g. after an attr update)."""
    result = await conn.execute(
        'UPDATE "03_iam"."10_fct_orgs" '
        'SET updated_by = $1, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by,
        id,
    )
    return result.endswith(" 1")


async def soft_delete_org(
    conn: Any,
    *,
    id: str,
    updated_by: str,
) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."10_fct_orgs" '
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
    org_id: str,
    display_name: str,
    attr_row_id: str,
) -> None:
    """
    Upsert the display_name EAV row for an org. attr_row_id is a caller-generated
    UUID v7 used only when inserting (conflict path leaves the existing id intact).
    """
    attr_def_id = await _get_display_name_attr_def_id(conn)
    await conn.execute(
        'INSERT INTO "03_iam"."21_dtl_attrs" '
        '    (id, entity_type_id, entity_id, attr_def_id, key_text) '
        'VALUES ($1, $2, $3, $4, $5) '
        'ON CONFLICT (entity_type_id, entity_id, attr_def_id) '
        '    DO UPDATE SET key_text = EXCLUDED.key_text',
        attr_row_id,
        _ORG_ENTITY_TYPE_ID,
        org_id,
        attr_def_id,
        display_name,
    )

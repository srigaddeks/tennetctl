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


async def list_scope_ids(conn: Any, application_id: str) -> list[int]:
    rows = await conn.fetch(
        'SELECT scope_id FROM "03_iam"."45_lnk_application_scopes" '
        'WHERE application_id = $1 ORDER BY scope_id',
        application_id,
    )
    return [int(r["scope_id"]) for r in rows]


async def list_scope_ids_many(conn: Any, application_ids: list[str]) -> dict[str, list[int]]:
    if not application_ids:
        return {}
    rows = await conn.fetch(
        'SELECT application_id, scope_id '
        'FROM "03_iam"."45_lnk_application_scopes" '
        'WHERE application_id = ANY($1::varchar[]) '
        'ORDER BY application_id, scope_id',
        application_ids,
    )
    out: dict[str, list[int]] = {aid: [] for aid in application_ids}
    for r in rows:
        out[r["application_id"]].append(int(r["scope_id"]))
    return out


async def replace_application_scopes(
    conn: Any, *,
    application_id: str, org_id: str, scope_ids: list[int], created_by: str,
) -> None:
    """Atomic REPLACE: delete existing rows + insert the new set. Caller must hold a tx."""
    await conn.execute(
        'DELETE FROM "03_iam"."45_lnk_application_scopes" WHERE application_id = $1',
        application_id,
    )
    if not scope_ids:
        return
    # Deduplicate defensively — service validates, but belt-and-suspenders keeps the
    # UNIQUE constraint from firing on caller typos.
    unique_ids = sorted(set(scope_ids))
    _core_id: Any = __import__("importlib").import_module("backend.01_core.id")
    records = [
        (_core_id.uuid7(), org_id, application_id, sid, created_by)
        for sid in unique_ids
    ]
    await conn.executemany(
        'INSERT INTO "03_iam"."45_lnk_application_scopes" '
        '    (id, org_id, application_id, scope_id, created_by) '
        'VALUES ($1, $2, $3, $4, $5)',
        records,
    )


async def dim_scope_ids_exist(conn: Any, scope_ids: list[int]) -> set[int]:
    if not scope_ids:
        return set()
    rows = await conn.fetch(
        'SELECT id FROM "03_iam"."03_dim_scopes" WHERE id = ANY($1::smallint[])',
        scope_ids,
    )
    return {int(r["id"]) for r in rows}


async def soft_delete_application(conn: Any, *, id: str, updated_by: str) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."15_fct_applications" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by, id,
    )
    return result.endswith(" 1")

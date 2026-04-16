"""featureflags.overrides — asyncpg repository."""
from __future__ import annotations

from typing import Any

_SENTINEL = object()

_COLS = (
    "id, flag_id, environment, entity_type, entity_id, value, reason, "
    "is_active, is_test, created_by, updated_by, created_at, updated_at"
)


async def get_env_id(conn: Any, code: str) -> int | None:
    return await conn.fetchval(
        'SELECT id FROM "09_featureflags"."01_dim_environments" WHERE code = $1',
        code,
    )


async def get_entity_type_id(conn: Any, code: str) -> int | None:
    return await conn.fetchval(
        'SELECT id FROM "03_iam"."01_dim_entity_types" WHERE code = $1',
        code,
    )


async def get_by_id(conn: Any, id: str) -> dict | None:
    row = await conn.fetchrow(
        f'SELECT {_COLS} FROM "09_featureflags"."v_overrides" '
        'WHERE id = $1 AND deleted_at IS NULL',
        id,
    )
    return dict(row) if row else None


async def get_by_key(
    conn: Any, *,
    flag_id: str, environment_id: int, entity_type_id: int, entity_id: str,
) -> dict | None:
    row_id = await conn.fetchval(
        'SELECT id FROM "09_featureflags"."21_fct_overrides" '
        'WHERE flag_id = $1 AND environment_id = $2 '
        '  AND entity_type_id = $3 AND entity_id = $4 '
        '  AND deleted_at IS NULL',
        flag_id, environment_id, entity_type_id, entity_id,
    )
    if row_id is None:
        return None
    return await get_by_id(conn, row_id)


async def list_overrides(
    conn: Any, *,
    limit: int, offset: int,
    flag_id: str | None = None,
    environment: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    where = ["deleted_at IS NULL"]
    params: list[Any] = []
    if flag_id:
        params.append(flag_id); where.append(f"flag_id = ${len(params)}")
    if environment:
        params.append(environment); where.append(f"environment = ${len(params)}")
    if entity_type:
        params.append(entity_type); where.append(f"entity_type = ${len(params)}")
    if entity_id:
        params.append(entity_id); where.append(f"entity_id = ${len(params)}")
    if is_active is not None:
        params.append(is_active); where.append(f"is_active = ${len(params)}")
    where_sql = " AND ".join(where)
    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "09_featureflags"."v_overrides" WHERE {where_sql}',
        *params,
    )
    params_page = [*params, limit, offset]
    l_idx, o_idx = len(params_page) - 1, len(params_page)
    rows = await conn.fetch(
        f'SELECT {_COLS} FROM "09_featureflags"."v_overrides" '
        f'WHERE {where_sql} '
        f'ORDER BY created_at DESC, id DESC '
        f'LIMIT ${l_idx} OFFSET ${o_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def list_overrides_for_eval(
    conn: Any, *, flag_id: str, environment_id: int, entity_pairs: list[tuple[int, str]],
) -> list[dict]:
    """Fast path for evaluator — returns active overrides matching any of the given
    (entity_type_id, entity_id) pairs, for a single (flag, env).
    """
    if not entity_pairs:
        return []
    rows = await conn.fetch(
        """
        SELECT o.id, o.value_jsonb AS value, o.entity_type_id, o.entity_id, e.code AS entity_type_code
        FROM "09_featureflags"."21_fct_overrides" o
        JOIN "03_iam"."01_dim_entity_types" e ON e.id = o.entity_type_id
        WHERE o.flag_id = $1 AND o.environment_id = $2
          AND o.deleted_at IS NULL AND o.is_active = true
          AND (o.entity_type_id, o.entity_id) = ANY($3::record[])
        """,
        flag_id, environment_id,
        [(et_id, eid) for et_id, eid in entity_pairs],
    )
    return [dict(r) for r in rows]


async def insert_override(
    conn: Any, *,
    id: str, flag_id: str, environment_id: int,
    entity_type_id: int, entity_id: str,
    value: Any, reason: str | None, created_by: str,
) -> None:
    await conn.execute(
        'INSERT INTO "09_featureflags"."21_fct_overrides" '
        '  (id, flag_id, environment_id, entity_type_id, entity_id, '
        '   value_jsonb, reason, created_by, updated_by) '
        'VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)',
        id, flag_id, environment_id, entity_type_id, entity_id,
        value, reason, created_by,
    )


async def update_override_fields(
    conn: Any, *,
    id: str,
    value: Any = _SENTINEL,
    reason: Any = _SENTINEL,
    is_active: Any = _SENTINEL,
    updated_by: str,
) -> bool:
    sets: list[str] = []
    params: list[Any] = []
    if value is not _SENTINEL:
        params.append(value); sets.append(f"value_jsonb = ${len(params)}")
    if reason is not _SENTINEL:
        params.append(reason); sets.append(f"reason = ${len(params)}")
    if is_active is not _SENTINEL:
        params.append(is_active); sets.append(f"is_active = ${len(params)}")
    if not sets:
        return False
    params.append(updated_by); params.append(id)
    sets.append(f"updated_by = ${len(params) - 1}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    result = await conn.execute(
        f'UPDATE "09_featureflags"."21_fct_overrides" SET {", ".join(sets)} '
        f'WHERE id = ${len(params)} AND deleted_at IS NULL',
        *params,
    )
    return result.endswith(" 1")


async def soft_delete_override(
    conn: Any, *, id: str, updated_by: str,
) -> bool:
    result = await conn.execute(
        'UPDATE "09_featureflags"."21_fct_overrides" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_by = $1, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by, id,
    )
    return result.endswith(" 1")

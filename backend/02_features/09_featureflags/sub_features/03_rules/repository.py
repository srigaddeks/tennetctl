"""featureflags.rules — asyncpg repository."""
from __future__ import annotations

from typing import Any

_SENTINEL = object()

_COLS = (
    "id, flag_id, environment, priority, conditions, value, "
    "rollout_percentage, is_active, is_test, "
    "created_by, updated_by, created_at, updated_at"
)


async def get_env_id(conn: Any, code: str) -> int | None:
    return await conn.fetchval(
        'SELECT id FROM "09_featureflags"."01_dim_environments" WHERE code = $1',
        code,
    )


async def get_by_id(conn: Any, id: str) -> dict | None:
    row = await conn.fetchrow(
        f'SELECT {_COLS} FROM "09_featureflags"."v_rules" '
        'WHERE id = $1 AND deleted_at IS NULL',
        id,
    )
    return dict(row) if row else None


async def list_rules(
    conn: Any, *,
    limit: int, offset: int,
    flag_id: str | None = None,
    environment: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    where = ["deleted_at IS NULL"]
    params: list[Any] = []
    if flag_id is not None:
        params.append(flag_id); where.append(f"flag_id = ${len(params)}")
    if environment is not None:
        params.append(environment); where.append(f"environment = ${len(params)}")
    if is_active is not None:
        params.append(is_active); where.append(f"is_active = ${len(params)}")
    where_sql = " AND ".join(where)
    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "09_featureflags"."v_rules" WHERE {where_sql}',
        *params,
    )
    params_page = [*params, limit, offset]
    l_idx, o_idx = len(params_page) - 1, len(params_page)
    rows = await conn.fetch(
        f'SELECT {_COLS} FROM "09_featureflags"."v_rules" '
        f'WHERE {where_sql} '
        f'ORDER BY flag_id, environment, priority ASC '
        f'LIMIT ${l_idx} OFFSET ${o_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def list_rules_for_eval(
    conn: Any, *, flag_id: str, environment_id: int,
) -> list[dict]:
    """Fast path for evaluator — returns rules in priority order, active only."""
    rows = await conn.fetch(
        'SELECT id, priority, conditions_jsonb AS conditions, value_jsonb AS value, '
        '       rollout_percentage '
        'FROM "09_featureflags"."20_fct_rules" '
        'WHERE flag_id = $1 AND environment_id = $2 '
        '  AND deleted_at IS NULL AND is_active = true '
        'ORDER BY priority ASC',
        flag_id, environment_id,
    )
    return [dict(r) for r in rows]


async def insert_rule(
    conn: Any, *,
    id: str, flag_id: str, environment_id: int, priority: int,
    conditions: dict, value: Any, rollout_percentage: int, created_by: str,
) -> None:
    await conn.execute(
        'INSERT INTO "09_featureflags"."20_fct_rules" '
        '  (id, flag_id, environment_id, priority, conditions_jsonb, '
        '   value_jsonb, rollout_percentage, created_by, updated_by) '
        'VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)',
        id, flag_id, environment_id, priority, conditions, value,
        rollout_percentage, created_by,
    )


async def update_rule_fields(
    conn: Any, *,
    id: str,
    priority: Any = _SENTINEL,
    conditions: Any = _SENTINEL,
    value: Any = _SENTINEL,
    rollout_percentage: Any = _SENTINEL,
    is_active: Any = _SENTINEL,
    updated_by: str,
) -> bool:
    sets: list[str] = []
    params: list[Any] = []
    if priority is not _SENTINEL:
        params.append(priority); sets.append(f"priority = ${len(params)}")
    if conditions is not _SENTINEL:
        params.append(conditions); sets.append(f"conditions_jsonb = ${len(params)}")
    if value is not _SENTINEL:
        params.append(value); sets.append(f"value_jsonb = ${len(params)}")
    if rollout_percentage is not _SENTINEL:
        params.append(rollout_percentage); sets.append(f"rollout_percentage = ${len(params)}")
    if is_active is not _SENTINEL:
        params.append(is_active); sets.append(f"is_active = ${len(params)}")
    if not sets:
        return False
    params.append(updated_by); params.append(id)
    sets.append(f"updated_by = ${len(params) - 1}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    result = await conn.execute(
        f'UPDATE "09_featureflags"."20_fct_rules" SET {", ".join(sets)} '
        f'WHERE id = ${len(params)} AND deleted_at IS NULL',
        *params,
    )
    return result.endswith(" 1")


async def soft_delete_rule(
    conn: Any, *, id: str, updated_by: str,
) -> bool:
    result = await conn.execute(
        'UPDATE "09_featureflags"."20_fct_rules" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_by = $1, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by, id,
    )
    return result.endswith(" 1")

"""Pipeline stages repository — raw asyncpg against schema "12_somacrm"."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somacrm.backend.01_core.id")

SCHEMA = '"12_somacrm"'
TABLE = f'{SCHEMA}."fct_pipeline_stages"'
VIEW = f'{SCHEMA}.v_pipeline_stages'


async def list_pipeline_stages(
    conn: Any, *, tenant_id: str, limit: int = 200, offset: int = 0,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {VIEW} WHERE tenant_id = $1 AND deleted_at IS NULL "
        f"ORDER BY order_position ASC LIMIT $2 OFFSET $3",
        tenant_id, limit, offset,
    )
    return [dict(r) for r in rows]


async def get_pipeline_stage(conn: Any, *, tenant_id: str, stage_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {VIEW} WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        stage_id, tenant_id,
    )
    return dict(row) if row else None


async def create_pipeline_stage(
    conn: Any, *, tenant_id: str, actor_user_id: str, data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {TABLE} "
        "(id, tenant_id, name, order_position, probability_pct, color, is_won, is_lost, "
        " properties, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$10)",
        new_id, tenant_id,
        data["name"],
        data.get("order_position", 0),
        data.get("probability_pct", 0),
        data.get("color", "#6366f1"),
        data.get("is_won", False),
        data.get("is_lost", False),
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(f"SELECT * FROM {VIEW} WHERE id = $1", new_id)
    return dict(row) if row else {}


async def update_pipeline_stage(
    conn: Any, *, tenant_id: str, actor_user_id: str, stage_id: str, patch: dict,
) -> dict | None:
    updatable = ("name", "order_position", "probability_pct", "color", "is_won", "is_lost", "properties")
    sets: list[str] = []
    params: list[Any] = []
    for col in updatable:
        if col in patch:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_pipeline_stage(conn, tenant_id=tenant_id, stage_id=stage_id)
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(stage_id)
    params.append(tenant_id)
    sql = (
        f'UPDATE {TABLE} SET {", ".join(sets)} '
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    row = await conn.fetchrow(f"SELECT * FROM {VIEW} WHERE id = $1", stage_id)
    return dict(row) if row else None


async def soft_delete_pipeline_stage(
    conn: Any, *, tenant_id: str, actor_user_id: str, stage_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {TABLE} "
        "SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, stage_id, tenant_id,
    )
    return result.endswith(" 1")

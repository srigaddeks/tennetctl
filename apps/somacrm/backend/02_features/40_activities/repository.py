"""Activities repository — raw asyncpg against schema "12_somacrm"."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somacrm.backend.01_core.id")

SCHEMA = '"12_somacrm"'
TABLE = f'{SCHEMA}."fct_activities"'
VIEW = f'{SCHEMA}.v_activities'


async def list_activities(
    conn: Any,
    *,
    tenant_id: str,
    activity_type_id: int | None = None,
    status_id: int | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    due_from: str | None = None,
    due_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1", "deleted_at IS NULL"]
    if activity_type_id is not None:
        params.append(activity_type_id)
        clauses.append(f"activity_type_id = ${len(params)}")
    if status_id is not None:
        params.append(status_id)
        clauses.append(f"status_id = ${len(params)}")
    if entity_type:
        params.append(entity_type)
        clauses.append(f"entity_type = ${len(params)}")
    if entity_id:
        params.append(entity_id)
        clauses.append(f"entity_id = ${len(params)}")
    if due_from:
        params.append(due_from)
        clauses.append(f"due_at >= ${len(params)}")
    if due_to:
        params.append(due_to)
        clauses.append(f"due_at <= ${len(params)}")
    params.extend([limit, offset])
    sql = (
        f"SELECT * FROM {VIEW} "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY due_at ASC NULLS LAST, created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_activity(conn: Any, *, tenant_id: str, activity_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {VIEW} WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        activity_id, tenant_id,
    )
    return dict(row) if row else None


async def create_activity(conn: Any, *, tenant_id: str, actor_user_id: str, data: dict) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {TABLE} "
        "(id, tenant_id, activity_type_id, status_id, title, description, "
        " due_at, completed_at, duration_minutes, entity_type, entity_id, "
        " assigned_to, properties, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$14)",
        new_id, tenant_id,
        data["activity_type_id"],
        data.get("status_id", 1),
        data["title"],
        data.get("description"),
        data.get("due_at"), data.get("completed_at"),
        data.get("duration_minutes"),
        data.get("entity_type"), data.get("entity_id"),
        data.get("assigned_to"),
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(f"SELECT * FROM {VIEW} WHERE id = $1", new_id)
    return dict(row) if row else {}


async def update_activity(
    conn: Any, *, tenant_id: str, actor_user_id: str, activity_id: str, patch: dict,
) -> dict | None:
    updatable = (
        "activity_type_id", "status_id", "title", "description",
        "due_at", "completed_at", "duration_minutes",
        "entity_type", "entity_id", "assigned_to", "properties",
    )
    sets: list[str] = []
    params: list[Any] = []
    for col in updatable:
        if col in patch:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_activity(conn, tenant_id=tenant_id, activity_id=activity_id)
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(activity_id)
    params.append(tenant_id)
    sql = (
        f'UPDATE {TABLE} SET {", ".join(sets)} '
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    row = await conn.fetchrow(f"SELECT * FROM {VIEW} WHERE id = $1", activity_id)
    return dict(row) if row else None


async def soft_delete_activity(
    conn: Any, *, tenant_id: str, actor_user_id: str, activity_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {TABLE} "
        "SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, activity_id, tenant_id,
    )
    return result.endswith(" 1")

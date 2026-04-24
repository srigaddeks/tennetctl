"""Notes repository — raw asyncpg against schema "12_somacrm"."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somacrm.backend.01_core.id")

SCHEMA = '"12_somacrm"'
TABLE = f'{SCHEMA}."fct_notes"'
VIEW = f'{SCHEMA}.v_notes'


async def list_notes(
    conn: Any,
    *,
    tenant_id: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1", "deleted_at IS NULL"]
    if entity_type:
        params.append(entity_type)
        clauses.append(f"entity_type = ${len(params)}")
    if entity_id:
        params.append(entity_id)
        clauses.append(f"entity_id = ${len(params)}")
    params.extend([limit, offset])
    sql = (
        f"SELECT * FROM {VIEW} "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY is_pinned DESC, created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_note(conn: Any, *, tenant_id: str, note_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {VIEW} WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        note_id, tenant_id,
    )
    return dict(row) if row else None


async def create_note(conn: Any, *, tenant_id: str, actor_user_id: str, data: dict) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {TABLE} "
        "(id, tenant_id, entity_type, entity_id, content, is_pinned, properties, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$8)",
        new_id, tenant_id,
        data["entity_type"], data["entity_id"],
        data["content"],
        data.get("is_pinned", False),
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(f"SELECT * FROM {VIEW} WHERE id = $1", new_id)
    return dict(row) if row else {}


async def update_note(
    conn: Any, *, tenant_id: str, actor_user_id: str, note_id: str, patch: dict,
) -> dict | None:
    updatable = ("content", "is_pinned", "properties")
    sets: list[str] = []
    params: list[Any] = []
    for col in updatable:
        if col in patch:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_note(conn, tenant_id=tenant_id, note_id=note_id)
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(note_id)
    params.append(tenant_id)
    sql = (
        f'UPDATE {TABLE} SET {", ".join(sets)} '
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    row = await conn.fetchrow(f"SELECT * FROM {VIEW} WHERE id = $1", note_id)
    return dict(row) if row else None


async def soft_delete_note(
    conn: Any, *, tenant_id: str, actor_user_id: str, note_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {TABLE} "
        "SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, note_id, tenant_id,
    )
    return result.endswith(" 1")

"""Kitchens repository — raw asyncpg against schema "11_somaerp"."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


async def list_kitchens(
    conn: Any,
    *,
    tenant_id: str,
    location_id: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1"]
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    if location_id is not None:
        params.append(location_id)
        clauses.append(f"location_id = ${len(params)}")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        clauses.append(f"name ILIKE ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_kitchens "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_kitchen(
    conn: Any, *, tenant_id: str, kitchen_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_kitchens "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        kitchen_id, tenant_id,
    )
    return dict(row) if row else None


async def get_location_exists(
    conn: Any, *, tenant_id: str, location_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_locations "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        location_id, tenant_id,
    )
    return row is not None


async def create_kitchen(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_kitchens "
        "(id, tenant_id, location_id, name, slug, kitchen_type, "
        " address_jsonb, geo_lat, geo_lng, status, properties, "
        " created_by, updated_by) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $12)",
        new_id,
        tenant_id,
        data["location_id"],
        data["name"],
        data["slug"],
        data["kitchen_type"],
        data.get("address_jsonb") or {},
        data.get("geo_lat"),
        data.get("geo_lng"),
        data.get("status") or "active",
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_kitchens WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_UPDATABLE_COLUMNS = (
    "location_id",
    "name",
    "slug",
    "kitchen_type",
    "address_jsonb",
    "geo_lat",
    "geo_lng",
    "status",
    "properties",
)


async def update_kitchen(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    kitchen_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _UPDATABLE_COLUMNS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_kitchen(
            conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(kitchen_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.fct_kitchens SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_kitchens WHERE id = $1", kitchen_id,
    )
    return dict(row) if row else None


async def soft_delete_kitchen(
    conn: Any, *, tenant_id: str, actor_user_id: str, kitchen_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_kitchens "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, kitchen_id, tenant_id,
    )
    return result.endswith(" 1")

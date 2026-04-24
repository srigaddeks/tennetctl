"""Service zones repository — raw asyncpg against schema "11_somaerp"."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


async def list_zones(
    conn: Any,
    *,
    tenant_id: str,
    kitchen_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1"]
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    if kitchen_id is not None:
        params.append(kitchen_id)
        clauses.append(f"kitchen_id = ${len(params)}")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_service_zones "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_zone(
    conn: Any, *, tenant_id: str, zone_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_service_zones "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        zone_id, tenant_id,
    )
    return dict(row) if row else None


async def get_kitchen_status(
    conn: Any, *, tenant_id: str, kitchen_id: str,
) -> str | None:
    """Return kitchen status if it exists and is not soft-deleted."""
    row = await conn.fetchrow(
        f"SELECT status FROM {SCHEMA}.fct_kitchens "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        kitchen_id, tenant_id,
    )
    return row["status"] if row else None


async def create_zone(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_service_zones "
        "(id, tenant_id, kitchen_id, name, polygon_jsonb, status, "
        " properties, created_by, updated_by) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)",
        new_id,
        tenant_id,
        data["kitchen_id"],
        data["name"],
        data.get("polygon_jsonb") or {},
        data.get("status") or "active",
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_service_zones WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_UPDATABLE_COLUMNS = (
    "kitchen_id",
    "name",
    "polygon_jsonb",
    "status",
    "properties",
)


async def update_zone(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    zone_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _UPDATABLE_COLUMNS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_zone(conn, tenant_id=tenant_id, zone_id=zone_id)
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(zone_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.fct_service_zones SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_service_zones WHERE id = $1", zone_id,
    )
    return dict(row) if row else None


async def soft_delete_zone(
    conn: Any, *, tenant_id: str, actor_user_id: str, zone_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_service_zones "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, zone_id, tenant_id,
    )
    return result.endswith(" 1")

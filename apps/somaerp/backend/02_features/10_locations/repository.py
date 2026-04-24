"""Locations repository — raw asyncpg against schema "11_somaerp".

Reads query v_regions / v_locations; writes go to fct_locations. All
functions take a `conn` (asyncpg.Connection); pool handling is routes-only.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Regions (read-only) ───────────────────────────────────────────────────

async def list_regions(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {SCHEMA}.v_regions "
        "WHERE deprecated_at IS NULL "
        "ORDER BY code ASC"
    )
    return [dict(r) for r in rows]


async def get_region(conn: Any, *, region_id: int) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_regions WHERE id = $1", region_id,
    )
    return dict(row) if row else None


# ── Locations CRUD ────────────────────────────────────────────────────────

async def list_locations(
    conn: Any,
    *,
    tenant_id: str,
    region_id: int | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1"]
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    if region_id is not None:
        params.append(region_id)
        clauses.append(f"region_id = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        clauses.append(f"name ILIKE ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_locations "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_location(
    conn: Any, *, tenant_id: str, location_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_locations "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        location_id, tenant_id,
    )
    return dict(row) if row else None


async def create_location(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_locations "
        "(id, tenant_id, region_id, name, slug, timezone, properties, "
        " created_by, updated_by) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)",
        new_id,
        tenant_id,
        data["region_id"],
        data["name"],
        data["slug"],
        data["timezone"],
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_locations WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


async def update_location(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    location_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in ("region_id", "name", "slug", "timezone", "properties"):
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        # No changes — return existing row.
        return await get_location(
            conn, tenant_id=tenant_id, location_id=location_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(location_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.fct_locations SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_locations WHERE id = $1", location_id,
    )
    return dict(row) if row else None


async def soft_delete_location(
    conn: Any, *, tenant_id: str, actor_user_id: str, location_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_locations "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, location_id, tenant_id,
    )
    return result.endswith(" 1")

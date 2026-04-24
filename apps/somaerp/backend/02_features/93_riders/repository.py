"""Riders repository — raw asyncpg.

Reads fct_riders directly (joined with dim_rider_roles) — no v_riders view in
v0.9.0. Writes fct_riders (soft-delete).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


_RIDER_SELECT = (
    "SELECT r.id, r.tenant_id, r.user_id, r.name, r.phone, r.role_id, "
    "       dr.name AS role_name, dr.code AS role_code, "
    "       r.vehicle_type, r.license_number, r.status, r.properties, "
    "       r.created_at, r.updated_at, r.created_by, r.updated_by, r.deleted_at "
    f"FROM {SCHEMA}.fct_riders r "
    f"LEFT JOIN {SCHEMA}.dim_rider_roles dr ON dr.id = r.role_id"
)


# ── Roles (read-only) ───────────────────────────────────────────────────


async def list_roles(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT id, code, name, deprecated_at "
        f"FROM {SCHEMA}.dim_rider_roles "
        "WHERE deprecated_at IS NULL "
        "ORDER BY id ASC"
    )
    return [dict(r) for r in rows]


async def role_exists(conn: Any, *, role_id: int) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.dim_rider_roles "
        "WHERE id = $1 AND deprecated_at IS NULL",
        role_id,
    )
    return row is not None


# ── Riders CRUD ────────────────────────────────────────────────────────


async def list_riders(
    conn: Any,
    *,
    tenant_id: str,
    status: str | None = None,
    role_id: int | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["r.tenant_id = $1"]
    if not include_deleted:
        clauses.append("r.deleted_at IS NULL")
    if status is not None:
        params.append(status)
        clauses.append(f"r.status = ${len(params)}")
    if role_id is not None:
        params.append(role_id)
        clauses.append(f"r.role_id = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        clauses.append(
            f"(r.name ILIKE ${len(params)} OR r.phone ILIKE ${len(params)})"
        )
    params.append(limit)
    params.append(offset)
    sql = (
        f"{_RIDER_SELECT} "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY r.created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_rider(
    conn: Any, *, tenant_id: str, rider_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"{_RIDER_SELECT} "
        "WHERE r.id = $1 AND r.tenant_id = $2 AND r.deleted_at IS NULL",
        rider_id, tenant_id,
    )
    return dict(row) if row else None


async def create_rider(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_riders "
        "(id, tenant_id, user_id, name, phone, role_id, "
        " vehicle_type, license_number, status, properties, "
        " created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$11)",
        new_id,
        tenant_id,
        data.get("user_id"),
        data["name"],
        data.get("phone"),
        int(data["role_id"]),
        data.get("vehicle_type"),
        data.get("license_number"),
        data.get("status") or "active",
        data.get("properties") or {},
        actor_user_id,
    )
    return await get_rider(conn, tenant_id=tenant_id, rider_id=new_id) or {}


_RIDER_COLS = (
    "user_id",
    "name",
    "phone",
    "role_id",
    "vehicle_type",
    "license_number",
    "status",
    "properties",
)


async def update_rider(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    rider_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _RIDER_COLS:
        if col in patch:
            value = patch[col]
            # Allow explicit None for user_id (clear link).
            if value is None and col != "user_id":
                continue
            params.append(value)
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_rider(
            conn, tenant_id=tenant_id, rider_id=rider_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(rider_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.fct_riders SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_rider(conn, tenant_id=tenant_id, rider_id=rider_id)


async def soft_delete_rider(
    conn: Any, *, tenant_id: str, actor_user_id: str, rider_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_riders "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, rider_id, tenant_id,
    )
    return result.endswith(" 1")

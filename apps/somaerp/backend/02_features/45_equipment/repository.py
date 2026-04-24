"""Equipment + kitchen-equipment link repository — raw asyncpg.

Schema: "11_somaerp".
- Reads hit v_equipment + v_kitchen_equipment.
- Writes to fct_equipment (soft-delete) and lnk_kitchen_equipment (IMMUTABLE,
  hard-delete only).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Categories (read-only) ──────────────────────────────────────────────


async def list_categories(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT id, code, name, deprecated_at "
        f"FROM {SCHEMA}.dim_equipment_categories "
        "WHERE deprecated_at IS NULL "
        "ORDER BY id ASC"
    )
    return [dict(r) for r in rows]


async def category_exists(conn: Any, *, category_id: int) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.dim_equipment_categories "
        "WHERE id = $1 AND deprecated_at IS NULL",
        category_id,
    )
    return row is not None


# ── Kitchen existence ───────────────────────────────────────────────────


async def kitchen_exists_for_tenant(
    conn: Any, *, tenant_id: str, kitchen_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_kitchens "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        kitchen_id, tenant_id,
    )
    return row is not None


# ── Equipment CRUD ──────────────────────────────────────────────────────


async def list_equipment(
    conn: Any,
    *,
    tenant_id: str,
    category_id: int | None = None,
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
    if category_id is not None:
        params.append(category_id)
        clauses.append(f"category_id = ${len(params)}")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        clauses.append(f"(name ILIKE ${len(params)} OR slug ILIKE ${len(params)})")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_equipment "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_equipment(
    conn: Any, *, tenant_id: str, equipment_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_equipment "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        equipment_id, tenant_id,
    )
    return dict(row) if row else None


async def create_equipment(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_equipment "
        "(id, tenant_id, category_id, name, slug, status, purchase_cost, "
        " currency_code, purchase_date, expected_lifespan_months, properties, "
        " created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$12)",
        new_id,
        tenant_id,
        int(data["category_id"]),
        data["name"],
        data["slug"],
        data.get("status") or "active",
        data.get("purchase_cost"),
        data.get("currency_code"),
        data.get("purchase_date"),
        data.get("expected_lifespan_months"),
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_equipment WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_EQUIPMENT_UPDATABLE_COLUMNS = (
    "category_id",
    "name",
    "slug",
    "status",
    "purchase_cost",
    "currency_code",
    "purchase_date",
    "expected_lifespan_months",
    "properties",
)


async def update_equipment(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    equipment_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _EQUIPMENT_UPDATABLE_COLUMNS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_equipment(
            conn, tenant_id=tenant_id, equipment_id=equipment_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(equipment_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.fct_equipment SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_equipment(
        conn, tenant_id=tenant_id, equipment_id=equipment_id,
    )


async def soft_delete_equipment(
    conn: Any, *, tenant_id: str, actor_user_id: str, equipment_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_equipment "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, equipment_id, tenant_id,
    )
    return result.endswith(" 1")


# ── Kitchen <-> Equipment link (IMMUTABLE) ──────────────────────────────


async def list_kitchen_equipment(
    conn: Any, *, tenant_id: str, kitchen_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {SCHEMA}.v_kitchen_equipment "
        "WHERE tenant_id = $1 AND kitchen_id = $2 "
        "ORDER BY created_at ASC",
        tenant_id, kitchen_id,
    )
    return [dict(r) for r in rows]


async def get_kitchen_equipment_link(
    conn: Any, *, tenant_id: str, kitchen_id: str, equipment_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id FROM {SCHEMA}.lnk_kitchen_equipment "
        "WHERE tenant_id = $1 AND kitchen_id = $2 AND equipment_id = $3",
        tenant_id, kitchen_id, equipment_id,
    )
    return dict(row) if row else None


async def attach_equipment_to_kitchen(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    kitchen_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.lnk_kitchen_equipment "
        "(id, tenant_id, kitchen_id, equipment_id, quantity, notes, created_by) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7)",
        new_id,
        tenant_id,
        kitchen_id,
        data["equipment_id"],
        int(data.get("quantity") or 1),
        data.get("notes"),
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_kitchen_equipment WHERE id = $1",
        new_id,
    )
    return dict(row) if row else {}


async def detach_equipment_from_kitchen(
    conn: Any, *, tenant_id: str, kitchen_id: str, equipment_id: str,
) -> bool:
    result = await conn.execute(
        f"DELETE FROM {SCHEMA}.lnk_kitchen_equipment "
        "WHERE tenant_id = $1 AND kitchen_id = $2 AND equipment_id = $3",
        tenant_id, kitchen_id, equipment_id,
    )
    return result.endswith(" 1")

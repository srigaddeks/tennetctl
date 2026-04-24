"""Kitchen capacity repository — raw asyncpg against schema "11_somaerp"."""

from __future__ import annotations

from datetime import date, time
from decimal import Decimal
from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Validation helpers ────────────────────────────────────────────────


async def kitchen_exists_for_tenant(
    conn: Any, *, tenant_id: str, kitchen_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_kitchens "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        kitchen_id, tenant_id,
    )
    return row is not None


async def product_line_exists_for_tenant(
    conn: Any, *, tenant_id: str, product_line_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_product_lines "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        product_line_id, tenant_id,
    )
    return row is not None


async def unit_exists(
    conn: Any, *, unit_id: int,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.dim_units_of_measure "
        "WHERE id = $1 AND deprecated_at IS NULL",
        unit_id,
    )
    return row is not None


# ── Reads ─────────────────────────────────────────────────────────────


async def list_capacity(
    conn: Any,
    *,
    tenant_id: str,
    kitchen_id: str,
    product_line_id: str | None = None,
    valid_on: date | None = None,
    include_history: bool = False,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    view = (
        f"{SCHEMA}.v_kitchen_capacity_history"
        if include_history or valid_on is not None or include_deleted
        else f"{SCHEMA}.v_kitchen_current_capacity"
    )
    params: list[Any] = [tenant_id, kitchen_id]
    clauses = ["tenant_id = $1", "kitchen_id = $2"]
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    if product_line_id is not None:
        params.append(product_line_id)
        clauses.append(f"product_line_id = ${len(params)}")
    if valid_on is not None:
        params.append(valid_on)
        clauses.append(
            f"valid_from <= ${len(params)} "
            f"AND (valid_to IS NULL OR valid_to > ${len(params)})",
        )
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {view} "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY valid_from DESC, time_window_start ASC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_capacity(
    conn: Any, *, tenant_id: str, kitchen_id: str, capacity_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_kitchen_capacity_history "
        "WHERE id = $1 AND tenant_id = $2 AND kitchen_id = $3",
        capacity_id, tenant_id, kitchen_id,
    )
    return dict(row) if row else None


# ── Writes ────────────────────────────────────────────────────────────


async def create_capacity(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    kitchen_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_kitchen_capacity "
        "(id, tenant_id, kitchen_id, product_line_id, "
        " capacity_value, capacity_unit_id, "
        " time_window_start, time_window_end, "
        " valid_from, valid_to, properties, "
        " created_by, updated_by) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $12)",
        new_id,
        tenant_id,
        kitchen_id,
        data["product_line_id"],
        Decimal(str(data["capacity_value"])),
        int(data["capacity_unit_id"]),
        data["time_window_start"],
        data["time_window_end"],
        data["valid_from"],
        data.get("valid_to"),
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_kitchen_capacity_history WHERE id = $1",
        new_id,
    )
    return dict(row) if row else {}


async def close_capacity(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    kitchen_id: str,
    capacity_id: str,
    valid_to: date,
) -> dict | None:
    """Set valid_to on an active row. Returns None if already closed / missing."""
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_kitchen_capacity "
        "SET valid_to = $1, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $2 "
        "WHERE id = $3 AND tenant_id = $4 AND kitchen_id = $5 "
        "  AND valid_to IS NULL AND deleted_at IS NULL",
        valid_to, actor_user_id, capacity_id, tenant_id, kitchen_id,
    )
    if not result.endswith(" 1"):
        return None
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_kitchen_capacity_history WHERE id = $1",
        capacity_id,
    )
    return dict(row) if row else None


async def soft_delete_capacity(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    kitchen_id: str,
    capacity_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_kitchen_capacity "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND kitchen_id = $4 "
        "  AND deleted_at IS NULL",
        actor_user_id, capacity_id, tenant_id, kitchen_id,
    )
    return result.endswith(" 1")

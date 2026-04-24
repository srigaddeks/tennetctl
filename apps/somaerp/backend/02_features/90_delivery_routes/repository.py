"""Delivery routes + IMMUTABLE route<->customer link repository.

Reads v_delivery_routes. Writes fct_delivery_routes (soft-delete) +
lnk_route_customers (HARD insert / hard delete; reorder = DELETE all + INSERT
new positions atomically inside a transaction).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Existence checks ─────────────────────────────────────────────────────


async def kitchen_exists(
    conn: Any, *, tenant_id: str, kitchen_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_kitchens "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        kitchen_id, tenant_id,
    )
    return row is not None


async def customer_exists(
    conn: Any, *, tenant_id: str, customer_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_customers "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        customer_id, tenant_id,
    )
    return row is not None


# ── Routes CRUD ──────────────────────────────────────────────────────────


async def list_routes(
    conn: Any,
    *,
    tenant_id: str,
    kitchen_id: str | None = None,
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
    if kitchen_id is not None:
        params.append(kitchen_id)
        clauses.append(f"kitchen_id = ${len(params)}")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        clauses.append(
            f"(name ILIKE ${len(params)} OR area ILIKE ${len(params)} "
            f"OR slug ILIKE ${len(params)})"
        )
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_delivery_routes "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_route(
    conn: Any, *, tenant_id: str, route_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_delivery_routes "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        route_id, tenant_id,
    )
    return dict(row) if row else None


async def create_route(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_delivery_routes "
        "(id, tenant_id, kitchen_id, name, slug, area, "
        " target_window_start, target_window_end, status, properties, "
        " created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$11)",
        new_id,
        tenant_id,
        data["kitchen_id"],
        data["name"],
        data["slug"],
        data.get("area"),
        data.get("target_window_start"),
        data.get("target_window_end"),
        data.get("status") or "active",
        data.get("properties") or {},
        actor_user_id,
    )
    return await get_route(conn, tenant_id=tenant_id, route_id=new_id) or {}


_ROUTE_COLS = (
    "kitchen_id",
    "name",
    "slug",
    "area",
    "target_window_start",
    "target_window_end",
    "status",
    "properties",
)


async def update_route(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    route_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _ROUTE_COLS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_route(conn, tenant_id=tenant_id, route_id=route_id)
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(route_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.fct_delivery_routes SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_route(conn, tenant_id=tenant_id, route_id=route_id)


async def soft_delete_route(
    conn: Any, *, tenant_id: str, actor_user_id: str, route_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_delivery_routes "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, route_id, tenant_id,
    )
    return result.endswith(" 1")


# ── Route customers (lnk_) ───────────────────────────────────────────────


async def list_route_customers(
    conn: Any, *, tenant_id: str, route_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT lrc.id, lrc.tenant_id, lrc.route_id, lrc.customer_id, "
        f"       lrc.sequence_position, lrc.created_at, lrc.created_by, "
        f"       c.name AS customer_name, c.phone AS customer_phone, "
        f"       c.address_jsonb AS customer_address "
        f"FROM {SCHEMA}.lnk_route_customers lrc "
        f"LEFT JOIN {SCHEMA}.fct_customers c ON c.id = lrc.customer_id "
        f"WHERE lrc.route_id = $1 AND lrc.tenant_id = $2 "
        f"ORDER BY lrc.sequence_position ASC",
        route_id, tenant_id,
    )
    return [dict(r) for r in rows]


async def _get_link(
    conn: Any, *, tenant_id: str, route_id: str, customer_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT lrc.id, lrc.tenant_id, lrc.route_id, lrc.customer_id, "
        f"       lrc.sequence_position, lrc.created_at, lrc.created_by, "
        f"       c.name AS customer_name, c.phone AS customer_phone, "
        f"       c.address_jsonb AS customer_address "
        f"FROM {SCHEMA}.lnk_route_customers lrc "
        f"LEFT JOIN {SCHEMA}.fct_customers c ON c.id = lrc.customer_id "
        f"WHERE lrc.tenant_id = $1 AND lrc.route_id = $2 "
        f"AND lrc.customer_id = $3",
        tenant_id, route_id, customer_id,
    )
    return dict(row) if row else None


async def attach_customer(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    route_id: str,
    customer_id: str,
    sequence_position: int | None,
) -> dict:
    # Compute next sequence_position if not provided.
    if sequence_position is None:
        row = await conn.fetchrow(
            f"SELECT COALESCE(MAX(sequence_position), 0) + 1 AS next "
            f"FROM {SCHEMA}.lnk_route_customers "
            f"WHERE route_id = $1 AND tenant_id = $2",
            route_id, tenant_id,
        )
        sequence_position = int(row["next"]) if row else 1

    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.lnk_route_customers "
        "(id, tenant_id, route_id, customer_id, sequence_position, created_by) "
        "VALUES ($1,$2,$3,$4,$5,$6)",
        new_id,
        tenant_id,
        route_id,
        customer_id,
        int(sequence_position),
        actor_user_id,
    )
    return await _get_link(
        conn,
        tenant_id=tenant_id,
        route_id=route_id,
        customer_id=customer_id,
    ) or {}


async def detach_customer(
    conn: Any,
    *,
    tenant_id: str,
    route_id: str,
    customer_id: str,
) -> bool:
    """Hard delete (no deleted_at on lnk_)."""
    result = await conn.execute(
        f"DELETE FROM {SCHEMA}.lnk_route_customers "
        f"WHERE tenant_id = $1 AND route_id = $2 AND customer_id = $3",
        tenant_id, route_id, customer_id,
    )
    return result.endswith(" 1")


async def reorder_customers(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    route_id: str,
    customer_ids: list[str],
) -> list[dict]:
    """Atomic DELETE all rows for route + INSERT new rows in given order.
    Returns the new ordered list."""
    async with conn.transaction():
        await conn.execute(
            f"DELETE FROM {SCHEMA}.lnk_route_customers "
            f"WHERE tenant_id = $1 AND route_id = $2",
            tenant_id, route_id,
        )
        for idx, cid in enumerate(customer_ids, start=1):
            new_id = _id.uuid7()
            await conn.execute(
                f"INSERT INTO {SCHEMA}.lnk_route_customers "
                "(id, tenant_id, route_id, customer_id, sequence_position, "
                " created_by) "
                "VALUES ($1,$2,$3,$4,$5,$6)",
                new_id,
                tenant_id,
                route_id,
                cid,
                idx,
                actor_user_id,
            )
    return await list_route_customers(
        conn, tenant_id=tenant_id, route_id=route_id,
    )


async def link_exists(
    conn: Any, *, tenant_id: str, route_id: str, customer_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.lnk_route_customers "
        f"WHERE tenant_id = $1 AND route_id = $2 AND customer_id = $3",
        tenant_id, route_id, customer_id,
    )
    return row is not None

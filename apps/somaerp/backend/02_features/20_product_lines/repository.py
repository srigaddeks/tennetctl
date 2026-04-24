"""Product lines repository — raw asyncpg against schema "11_somaerp"."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Categories (read-only) ───────────────────────────────────────────────

async def list_categories(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT id, code, name, deprecated_at "
        f"FROM {SCHEMA}.dim_product_categories "
        "WHERE deprecated_at IS NULL "
        "ORDER BY id ASC"
    )
    return [dict(r) for r in rows]


async def get_category(conn: Any, *, category_id: int) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id, code, name, deprecated_at "
        f"FROM {SCHEMA}.dim_product_categories WHERE id = $1",
        category_id,
    )
    return dict(row) if row else None


# ── Product lines CRUD ───────────────────────────────────────────────────

async def list_product_lines(
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
        clauses.append(f"name ILIKE ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_product_lines "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_product_line(
    conn: Any, *, tenant_id: str, product_line_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_product_lines "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        product_line_id, tenant_id,
    )
    return dict(row) if row else None


async def create_product_line(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_product_lines "
        "(id, tenant_id, category_id, name, slug, status, properties, "
        " created_by, updated_by) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)",
        new_id,
        tenant_id,
        data["category_id"],
        data["name"],
        data["slug"],
        data.get("status") or "active",
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_product_lines WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_UPDATABLE_COLUMNS = (
    "category_id",
    "name",
    "slug",
    "status",
    "properties",
)


async def update_product_line(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    product_line_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _UPDATABLE_COLUMNS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_product_line(
            conn, tenant_id=tenant_id, product_line_id=product_line_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(product_line_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.fct_product_lines SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_product_lines WHERE id = $1", product_line_id,
    )
    return dict(row) if row else None


async def soft_delete_product_line(
    conn: Any, *, tenant_id: str, actor_user_id: str, product_line_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_product_lines "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, product_line_id, tenant_id,
    )
    return result.endswith(" 1")


async def has_active_products(
    conn: Any, *, tenant_id: str, product_line_id: str,
) -> bool:
    """True if at least one non-deleted fct_products row references this line."""
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_products "
        "WHERE product_line_id = $1 AND tenant_id = $2 "
        "AND deleted_at IS NULL LIMIT 1",
        product_line_id, tenant_id,
    )
    return row is not None

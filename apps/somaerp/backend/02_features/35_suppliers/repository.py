"""Suppliers + material<->supplier link repository — raw asyncpg.

Schema: "11_somaerp".
- Reads hit v_suppliers and v_raw_material_supplier_matrix.
- Writes to fct_suppliers (soft-delete) + lnk_raw_material_suppliers
  (MUTABLE per spec deviation, hard-delete on unlink).
- is_primary on the link is atomically replaced inside a tx.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Source-type reads ────────────────────────────────────────────────────


async def list_source_types(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT id, code, name, deprecated_at "
        f"FROM {SCHEMA}.dim_supplier_source_types "
        "WHERE deprecated_at IS NULL "
        "ORDER BY id ASC"
    )
    return [dict(r) for r in rows]


async def get_source_type(conn: Any, *, source_type_id: int) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id, code, name, deprecated_at "
        f"FROM {SCHEMA}.dim_supplier_source_types "
        "WHERE id = $1 AND deprecated_at IS NULL",
        source_type_id,
    )
    return dict(row) if row else None


# ── Location existence check (cross-sub-feature read) ────────────────────


async def location_exists(
    conn: Any, *, tenant_id: str, location_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_locations "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        location_id, tenant_id,
    )
    return row is not None


# ── Raw material existence check (cross-sub-feature) ─────────────────────


async def raw_material_exists(
    conn: Any, *, tenant_id: str, material_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_raw_materials "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        material_id, tenant_id,
    )
    return row is not None


# ── Suppliers CRUD ───────────────────────────────────────────────────────


async def list_suppliers(
    conn: Any,
    *,
    tenant_id: str,
    source_type_id: int | None = None,
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
    if source_type_id is not None:
        params.append(source_type_id)
        clauses.append(f"source_type_id = ${len(params)}")
    if location_id is not None:
        params.append(location_id)
        clauses.append(f"location_id = ${len(params)}")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        clauses.append(f"(name ILIKE ${len(params)} OR slug ILIKE ${len(params)})")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_suppliers "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_supplier(
    conn: Any, *, tenant_id: str, supplier_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_suppliers "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        supplier_id, tenant_id,
    )
    return dict(row) if row else None


async def create_supplier(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_suppliers "
        "(id, tenant_id, name, slug, source_type_id, location_id, "
        " contact_jsonb, payment_terms, default_currency_code, "
        " quality_rating, status, properties, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$13)",
        new_id,
        tenant_id,
        data["name"],
        data["slug"],
        data["source_type_id"],
        data.get("location_id"),
        data.get("contact_jsonb") or {},
        data.get("payment_terms"),
        data["default_currency_code"],
        data.get("quality_rating"),
        data.get("status") or "active",
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_suppliers WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_SUPPLIER_UPDATABLE_COLUMNS = (
    "name",
    "slug",
    "source_type_id",
    "location_id",
    "contact_jsonb",
    "payment_terms",
    "default_currency_code",
    "quality_rating",
    "status",
    "properties",
)


async def update_supplier(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    supplier_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _SUPPLIER_UPDATABLE_COLUMNS:
        # Allow explicit None for location_id (means clear).
        if col in patch:
            value = patch[col]
            if value is None and col != "location_id":
                continue
            params.append(value)
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_supplier(
            conn, tenant_id=tenant_id, supplier_id=supplier_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(supplier_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.fct_suppliers SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_supplier(
        conn, tenant_id=tenant_id, supplier_id=supplier_id,
    )


async def soft_delete_supplier(
    conn: Any, *, tenant_id: str, actor_user_id: str, supplier_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_suppliers "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, supplier_id, tenant_id,
    )
    return result.endswith(" 1")


# ── Material <-> Supplier links ──────────────────────────────────────────


async def list_supplier_links_for_material(
    conn: Any, *, tenant_id: str, material_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {SCHEMA}.v_raw_material_supplier_matrix "
        "WHERE tenant_id = $1 AND raw_material_id = $2 "
        "ORDER BY is_primary DESC, created_at ASC",
        tenant_id, material_id,
    )
    return [dict(r) for r in rows]


async def list_material_links_for_supplier(
    conn: Any, *, tenant_id: str, supplier_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {SCHEMA}.v_raw_material_supplier_matrix "
        "WHERE tenant_id = $1 AND supplier_id = $2 "
        "ORDER BY is_primary DESC, created_at ASC",
        tenant_id, supplier_id,
    )
    return [dict(r) for r in rows]


async def get_link(
    conn: Any, *, tenant_id: str, material_id: str, supplier_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_raw_material_supplier_matrix "
        "WHERE tenant_id = $1 AND raw_material_id = $2 AND supplier_id = $3",
        tenant_id, material_id, supplier_id,
    )
    return dict(row) if row else None


async def get_link_raw(
    conn: Any, *, tenant_id: str, material_id: str, supplier_id: str,
) -> dict | None:
    """Raw row from lnk_raw_material_suppliers (needed for prior-primary diff)."""
    row = await conn.fetchrow(
        f"SELECT id, is_primary, last_known_unit_cost, currency_code, notes "
        f"FROM {SCHEMA}.lnk_raw_material_suppliers "
        "WHERE tenant_id = $1 AND raw_material_id = $2 AND supplier_id = $3",
        tenant_id, material_id, supplier_id,
    )
    return dict(row) if row else None


async def create_link(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    material_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    async with conn.transaction():
        if data.get("is_primary"):
            # Atomically clear any existing primary for this material.
            await conn.execute(
                f"UPDATE {SCHEMA}.lnk_raw_material_suppliers "
                "SET is_primary = FALSE, "
                "    updated_at = CURRENT_TIMESTAMP, "
                "    updated_by = $1 "
                "WHERE tenant_id = $2 AND raw_material_id = $3 "
                "AND is_primary = TRUE",
                actor_user_id, tenant_id, material_id,
            )
        await conn.execute(
            f"INSERT INTO {SCHEMA}.lnk_raw_material_suppliers "
            "(id, tenant_id, raw_material_id, supplier_id, is_primary, "
            " last_known_unit_cost, currency_code, notes, "
            " created_by, updated_by) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$9)",
            new_id,
            tenant_id,
            material_id,
            data["supplier_id"],
            bool(data.get("is_primary")),
            data.get("last_known_unit_cost"),
            data["currency_code"],
            data.get("notes"),
            actor_user_id,
        )
    return await get_link(
        conn,
        tenant_id=tenant_id,
        material_id=material_id,
        supplier_id=data["supplier_id"],
    ) or {}


_LINK_UPDATABLE_COLUMNS = (
    "is_primary",
    "last_known_unit_cost",
    "currency_code",
    "notes",
)


async def update_link(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    material_id: str,
    supplier_id: str,
    patch: dict,
) -> dict | None:
    async with conn.transaction():
        if patch.get("is_primary") is True:
            # Clear any other primary for this material in same tx.
            await conn.execute(
                f"UPDATE {SCHEMA}.lnk_raw_material_suppliers "
                "SET is_primary = FALSE, "
                "    updated_at = CURRENT_TIMESTAMP, "
                "    updated_by = $1 "
                "WHERE tenant_id = $2 AND raw_material_id = $3 "
                "AND is_primary = TRUE AND supplier_id <> $4",
                actor_user_id, tenant_id, material_id, supplier_id,
            )

        sets: list[str] = []
        params: list[Any] = []
        for col in _LINK_UPDATABLE_COLUMNS:
            if col in patch and patch[col] is not None:
                params.append(patch[col])
                sets.append(f"{col} = ${len(params)}")
        if not sets:
            return await get_link(
                conn,
                tenant_id=tenant_id,
                material_id=material_id,
                supplier_id=supplier_id,
            )
        params.append(actor_user_id)
        sets.append(f"updated_by = ${len(params)}")
        sets.append("updated_at = CURRENT_TIMESTAMP")
        params.append(tenant_id)
        params.append(material_id)
        params.append(supplier_id)
        sql = (
            f"UPDATE {SCHEMA}.lnk_raw_material_suppliers "
            f"SET {', '.join(sets)} "
            f"WHERE tenant_id = ${len(params) - 2} "
            f"AND raw_material_id = ${len(params) - 1} "
            f"AND supplier_id = ${len(params)}"
        )
        result = await conn.execute(sql, *params)
        if not result.endswith(" 1"):
            return None
    return await get_link(
        conn,
        tenant_id=tenant_id,
        material_id=material_id,
        supplier_id=supplier_id,
    )


async def delete_link(
    conn: Any, *, tenant_id: str, material_id: str, supplier_id: str,
) -> bool:
    """Hard-delete the link (no deleted_at on lnk table)."""
    result = await conn.execute(
        f"DELETE FROM {SCHEMA}.lnk_raw_material_suppliers "
        "WHERE tenant_id = $1 AND raw_material_id = $2 AND supplier_id = $3",
        tenant_id, material_id, supplier_id,
    )
    return result.endswith(" 1")

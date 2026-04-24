"""Raw materials + variants + category/unit reads — raw asyncpg.

Schema: "11_somaerp".
- Reads hit v_raw_materials (no dedicated variant view; join in SQL inline).
- Writes go to fct_raw_materials / fct_raw_material_variants.
- Variant is_default is atomically replaced inside a tx.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Dim reads ────────────────────────────────────────────────────────────


async def list_categories(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT id, code, name, deprecated_at "
        f"FROM {SCHEMA}.dim_raw_material_categories "
        "WHERE deprecated_at IS NULL "
        "ORDER BY id ASC"
    )
    return [dict(r) for r in rows]


async def get_category(conn: Any, *, category_id: int) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id, code, name, deprecated_at "
        f"FROM {SCHEMA}.dim_raw_material_categories "
        "WHERE id = $1 AND deprecated_at IS NULL",
        category_id,
    )
    return dict(row) if row else None


async def list_units(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT id, code, name, dimension, base_unit_id, to_base_factor, "
        f"deprecated_at "
        f"FROM {SCHEMA}.dim_units_of_measure "
        "WHERE deprecated_at IS NULL "
        "ORDER BY id ASC"
    )
    return [dict(r) for r in rows]


async def get_unit(conn: Any, *, unit_id: int) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id, code, name, dimension, base_unit_id, to_base_factor, "
        f"deprecated_at "
        f"FROM {SCHEMA}.dim_units_of_measure "
        "WHERE id = $1 AND deprecated_at IS NULL",
        unit_id,
    )
    return dict(row) if row else None


# ── Raw materials CRUD ───────────────────────────────────────────────────


async def list_materials(
    conn: Any,
    *,
    tenant_id: str,
    category_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
    requires_lot_tracking: bool | None = None,
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
    if requires_lot_tracking is not None:
        params.append(requires_lot_tracking)
        clauses.append(f"requires_lot_tracking = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        clauses.append(f"(name ILIKE ${len(params)} OR slug ILIKE ${len(params)})")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_raw_materials "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_material(
    conn: Any, *, tenant_id: str, material_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_raw_materials "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        material_id, tenant_id,
    )
    return dict(row) if row else None


async def create_material(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_raw_materials "
        "(id, tenant_id, category_id, name, slug, default_unit_id, "
        " default_shelf_life_hours, requires_lot_tracking, target_unit_cost, "
        " currency_code, status, properties, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$13)",
        new_id,
        tenant_id,
        data["category_id"],
        data["name"],
        data["slug"],
        data["default_unit_id"],
        data.get("default_shelf_life_hours"),
        bool(data.get("requires_lot_tracking", True)),
        data.get("target_unit_cost"),
        data["currency_code"],
        data.get("status") or "active",
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_raw_materials WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_MATERIAL_UPDATABLE_COLUMNS = (
    "category_id",
    "name",
    "slug",
    "default_unit_id",
    "default_shelf_life_hours",
    "requires_lot_tracking",
    "target_unit_cost",
    "currency_code",
    "status",
    "properties",
)


async def update_material(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    material_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _MATERIAL_UPDATABLE_COLUMNS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_material(
            conn, tenant_id=tenant_id, material_id=material_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(material_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.fct_raw_materials SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_material(
        conn, tenant_id=tenant_id, material_id=material_id,
    )


async def soft_delete_material(
    conn: Any, *, tenant_id: str, actor_user_id: str, material_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_raw_materials "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, material_id, tenant_id,
    )
    return result.endswith(" 1")


# ── Raw material variants ────────────────────────────────────────────────

_VARIANT_SELECT = (
    "SELECT v.id, v.tenant_id, v.raw_material_id, "
    "       rm.name AS raw_material_name, rm.slug AS raw_material_slug, "
    "       v.name, v.slug, v.target_unit_cost, v.currency_code, "
    "       v.is_default, v.status, v.properties, "
    "       v.created_at, v.updated_at, v.created_by, v.updated_by, "
    "       v.deleted_at "
    f"FROM {SCHEMA}.fct_raw_material_variants v "
    f"LEFT JOIN {SCHEMA}.fct_raw_materials rm ON rm.id = v.raw_material_id "
)


async def list_variants(
    conn: Any,
    *,
    tenant_id: str,
    material_id: str,
    include_deleted: bool = False,
) -> list[dict]:
    clauses = ["v.tenant_id = $1", "v.raw_material_id = $2"]
    params: list[Any] = [tenant_id, material_id]
    if not include_deleted:
        clauses.append("v.deleted_at IS NULL")
    sql = (
        _VARIANT_SELECT
        + f"WHERE {' AND '.join(clauses)} "
        + "ORDER BY v.is_default DESC, v.created_at ASC"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_variant(
    conn: Any, *, tenant_id: str, material_id: str, variant_id: str,
) -> dict | None:
    sql = (
        _VARIANT_SELECT
        + "WHERE v.id = $1 AND v.tenant_id = $2 AND v.raw_material_id = $3 "
        + "AND v.deleted_at IS NULL"
    )
    row = await conn.fetchrow(sql, variant_id, tenant_id, material_id)
    return dict(row) if row else None


async def create_variant(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    material_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    async with conn.transaction():
        if data.get("is_default"):
            # Atomically clear any prior default variant in same tx.
            await conn.execute(
                f"UPDATE {SCHEMA}.fct_raw_material_variants "
                "SET is_default = FALSE, "
                "    updated_at = CURRENT_TIMESTAMP, "
                "    updated_by = $1 "
                "WHERE tenant_id = $2 AND raw_material_id = $3 "
                "AND is_default = TRUE AND deleted_at IS NULL",
                actor_user_id, tenant_id, material_id,
            )
        await conn.execute(
            f"INSERT INTO {SCHEMA}.fct_raw_material_variants "
            "(id, tenant_id, raw_material_id, name, slug, target_unit_cost, "
            " currency_code, is_default, status, properties, "
            " created_by, updated_by) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$11)",
            new_id,
            tenant_id,
            material_id,
            data["name"],
            data["slug"],
            data.get("target_unit_cost"),
            data["currency_code"],
            bool(data.get("is_default")),
            data.get("status") or "active",
            data.get("properties") or {},
            actor_user_id,
        )
    return await get_variant(
        conn, tenant_id=tenant_id, material_id=material_id, variant_id=new_id,
    ) or {}


_VARIANT_UPDATABLE_COLUMNS = (
    "name",
    "slug",
    "target_unit_cost",
    "currency_code",
    "is_default",
    "status",
    "properties",
)


async def update_variant(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    material_id: str,
    variant_id: str,
    patch: dict,
) -> dict | None:
    async with conn.transaction():
        if patch.get("is_default") is True:
            # Clear prior default in same tx (excluding self).
            await conn.execute(
                f"UPDATE {SCHEMA}.fct_raw_material_variants "
                "SET is_default = FALSE, "
                "    updated_at = CURRENT_TIMESTAMP, "
                "    updated_by = $1 "
                "WHERE tenant_id = $2 AND raw_material_id = $3 "
                "AND is_default = TRUE AND id <> $4 AND deleted_at IS NULL",
                actor_user_id, tenant_id, material_id, variant_id,
            )

        sets: list[str] = []
        params: list[Any] = []
        for col in _VARIANT_UPDATABLE_COLUMNS:
            if col in patch and patch[col] is not None:
                params.append(patch[col])
                sets.append(f"{col} = ${len(params)}")
        if not sets:
            return await get_variant(
                conn,
                tenant_id=tenant_id,
                material_id=material_id,
                variant_id=variant_id,
            )
        params.append(actor_user_id)
        sets.append(f"updated_by = ${len(params)}")
        sets.append("updated_at = CURRENT_TIMESTAMP")
        params.append(variant_id)
        params.append(tenant_id)
        params.append(material_id)
        sql = (
            f"UPDATE {SCHEMA}.fct_raw_material_variants SET {', '.join(sets)} "
            f"WHERE id = ${len(params) - 2} "
            f"AND tenant_id = ${len(params) - 1} "
            f"AND raw_material_id = ${len(params)} AND deleted_at IS NULL"
        )
        result = await conn.execute(sql, *params)
        if not result.endswith(" 1"):
            return None
    return await get_variant(
        conn,
        tenant_id=tenant_id,
        material_id=material_id,
        variant_id=variant_id,
    )


async def soft_delete_variant(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    material_id: str,
    variant_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_raw_material_variants "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND raw_material_id = $4 "
        "AND deleted_at IS NULL",
        actor_user_id, variant_id, tenant_id, material_id,
    )
    return result.endswith(" 1")

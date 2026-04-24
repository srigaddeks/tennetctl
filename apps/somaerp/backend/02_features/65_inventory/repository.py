"""Inventory repository — raw asyncpg.

Schema: "11_somaerp".
- Reads: v_inventory_current + v_inventory_movements.
- Writes: evt_inventory_movements (append-only; this repo is used only for
  the manual adjustments path — procurement-driven receives flow through
  02_features.60_procurement.repository._insert_movement).
- Also computes the MRP-lite plan against active recipes.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Existence checks ────────────────────────────────────────────────────


async def kitchen_exists(
    conn: Any, *, tenant_id: str, kitchen_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_kitchens "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        kitchen_id, tenant_id,
    )
    return row is not None


async def raw_material_exists(
    conn: Any, *, tenant_id: str, raw_material_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_raw_materials "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        raw_material_id, tenant_id,
    )
    return row is not None


async def unit_exists(conn: Any, *, unit_id: int) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.dim_units_of_measure "
        "WHERE id = $1 AND deprecated_at IS NULL",
        unit_id,
    )
    return row is not None


# ── Current inventory ───────────────────────────────────────────────────


async def list_current(
    conn: Any,
    *,
    tenant_id: str,
    kitchen_id: str | None = None,
    raw_material_id: str | None = None,
    category_id: int | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1"]
    if kitchen_id is not None:
        params.append(kitchen_id)
        clauses.append(f"kitchen_id = ${len(params)}")
    if raw_material_id is not None:
        params.append(raw_material_id)
        clauses.append(f"raw_material_id = ${len(params)}")
    if category_id is not None:
        params.append(category_id)
        clauses.append(f"category_id = ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_inventory_current "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY raw_material_name ASC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


# ── Movements feed ──────────────────────────────────────────────────────


async def list_movements(
    conn: Any,
    *,
    tenant_id: str,
    kitchen_id: str | None = None,
    raw_material_id: str | None = None,
    movement_type: str | None = None,
    ts_after: datetime | None = None,
    ts_before: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1"]
    if kitchen_id is not None:
        params.append(kitchen_id)
        clauses.append(f"kitchen_id = ${len(params)}")
    if raw_material_id is not None:
        params.append(raw_material_id)
        clauses.append(f"raw_material_id = ${len(params)}")
    if movement_type is not None:
        params.append(movement_type)
        clauses.append(f"movement_type = ${len(params)}")
    if ts_after is not None:
        params.append(ts_after)
        clauses.append(f"ts >= ${len(params)}")
    if ts_before is not None:
        params.append(ts_before)
        clauses.append(f"ts <= ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_inventory_movements "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY ts DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_movement(
    conn: Any, *, tenant_id: str, movement_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_inventory_movements "
        "WHERE id = $1 AND tenant_id = $2",
        movement_id, tenant_id,
    )
    return dict(row) if row else None


async def record_movement(
    conn: Any,
    *,
    tenant_id: str,
    performed_by_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.evt_inventory_movements "
        "(id, tenant_id, kitchen_id, raw_material_id, movement_type, "
        " quantity, unit_id, lot_number, batch_id_ref, procurement_run_id, "
        " reason, performed_by_user_id, metadata) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,NULL,NULL,$9,$10,$11)",
        new_id,
        tenant_id,
        data["kitchen_id"],
        data["raw_material_id"],
        data["movement_type"],
        data["quantity"],
        int(data["unit_id"]),
        data.get("lot_number"),
        data.get("reason"),
        performed_by_user_id,
        data.get("metadata") or {},
    )
    row = await get_movement(
        conn, tenant_id=tenant_id, movement_id=new_id,
    )
    return row or {}


# ── MRP-lite planner ────────────────────────────────────────────────────


async def _load_units(conn: Any) -> dict[int, dict]:
    rows = await conn.fetch(
        f"SELECT id, code, name, dimension, base_unit_id, to_base_factor "
        f"FROM {SCHEMA}.dim_units_of_measure "
        "WHERE deprecated_at IS NULL",
    )
    return {int(r["id"]): dict(r) for r in rows}


async def _load_raw_materials_for_tenant(
    conn: Any, *, tenant_id: str,
) -> dict[str, dict]:
    rows = await conn.fetch(
        f"SELECT rm.id, rm.name, rm.slug, rm.default_unit_id, "
        f"rm.target_unit_cost, rm.currency_code, rm.category_id, "
        f"cat.name AS category_name, u.code AS default_unit_code, "
        f"u.dimension AS default_unit_dimension, "
        f"u.to_base_factor AS default_unit_to_base "
        f"FROM {SCHEMA}.fct_raw_materials rm "
        f"LEFT JOIN {SCHEMA}.dim_raw_material_categories cat ON cat.id = rm.category_id "
        f"LEFT JOIN {SCHEMA}.dim_units_of_measure u ON u.id = rm.default_unit_id "
        f"WHERE rm.tenant_id = $1 AND rm.deleted_at IS NULL",
        tenant_id,
    )
    return {r["id"]: dict(r) for r in rows}


async def _get_active_recipe_id_for_product(
    conn: Any, *, tenant_id: str, product_id: str,
) -> str | None:
    row = await conn.fetchrow(
        f"SELECT id FROM {SCHEMA}.fct_recipes "
        "WHERE tenant_id = $1 AND product_id = $2 "
        "AND status = 'active' AND deleted_at IS NULL "
        "ORDER BY version DESC LIMIT 1",
        tenant_id, product_id,
    )
    return row["id"] if row else None


async def _load_active_recipe_ingredients(
    conn: Any, *, tenant_id: str, recipe_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT id, raw_material_id, quantity, unit_id "
        f"FROM {SCHEMA}.dtl_recipe_ingredients "
        "WHERE tenant_id = $1 AND recipe_id = $2 AND deleted_at IS NULL",
        tenant_id, recipe_id,
    )
    return [dict(r) for r in rows]


async def _get_primary_supplier(
    conn: Any, *, tenant_id: str, raw_material_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT lnk.supplier_id, s.name AS supplier_name, "
        f"lnk.last_known_unit_cost, lnk.currency_code "
        f"FROM {SCHEMA}.lnk_raw_material_suppliers lnk "
        f"JOIN {SCHEMA}.fct_suppliers s ON s.id = lnk.supplier_id "
        f"WHERE lnk.tenant_id = $1 AND lnk.raw_material_id = $2 "
        "AND lnk.is_primary = TRUE "
        "LIMIT 1",
        tenant_id, raw_material_id,
    )
    return dict(row) if row else None


async def _get_current_qty_in_default_unit(
    conn: Any, *, tenant_id: str, kitchen_id: str, raw_material_id: str,
) -> Decimal:
    row = await conn.fetchrow(
        f"SELECT qty_in_default_unit "
        f"FROM {SCHEMA}.v_inventory_current "
        "WHERE tenant_id = $1 AND kitchen_id = $2 AND raw_material_id = $3",
        tenant_id, kitchen_id, raw_material_id,
    )
    if row is None or row["qty_in_default_unit"] is None:
        return Decimal("0")
    return Decimal(str(row["qty_in_default_unit"]))


async def compute_plan(
    conn: Any,
    *,
    tenant_id: str,
    kitchen_id: str,
    demand: list[dict],
) -> dict:
    if not await kitchen_exists(
        conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
    ):
        return {
            "kitchen_id": kitchen_id,
            "horizon_start": None,
            "horizon_end": None,
            "requirements": [],
            "unconvertible_units": [],
            "errors": [{
                "code": "invalid_kitchen",
                "message": f"Kitchen {kitchen_id} not found for this tenant.",
            }],
            "total_estimated_cost": Decimal("0"),
            "currency_code": "INR",
        }

    units_map = await _load_units(conn)
    rm_map = await _load_raw_materials_for_tenant(conn, tenant_id=tenant_id)

    rollup: dict[str, Decimal] = {}
    unconvertible: list[dict] = []
    errors: list[dict] = []

    dates = [d["target_date"] for d in demand]
    horizon_start = min(dates) if dates else None
    horizon_end = max(dates) if dates else None

    for d in demand:
        product_id = d["product_id"]
        planned_qty = Decimal(str(d["planned_qty"]))

        recipe_id = await _get_active_recipe_id_for_product(
            conn, tenant_id=tenant_id, product_id=product_id,
        )
        if recipe_id is None:
            errors.append({
                "code": "no_active_recipe",
                "product_id": product_id,
                "message": (
                    f"No active recipe found for product {product_id} — "
                    "planner cannot explode BOM."
                ),
            })
            continue

        ingredients = await _load_active_recipe_ingredients(
            conn, tenant_id=tenant_id, recipe_id=recipe_id,
        )
        if not ingredients:
            errors.append({
                "code": "empty_recipe",
                "product_id": product_id,
                "message": (
                    f"Active recipe {recipe_id} for product {product_id} "
                    "has no ingredients."
                ),
            })
            continue

        for ing in ingredients:
            rm_id = ing["raw_material_id"]
            rm = rm_map.get(rm_id)
            if rm is None:
                errors.append({
                    "code": "raw_material_missing",
                    "product_id": product_id,
                    "raw_material_id": rm_id,
                    "message": (
                        f"Recipe references raw material {rm_id} which is "
                        "missing/deleted for this tenant."
                    ),
                })
                continue

            ing_unit = units_map.get(int(ing["unit_id"]))
            rm_default_unit = units_map.get(int(rm["default_unit_id"]))
            if ing_unit is None or rm_default_unit is None:
                unconvertible.append({
                    "product_id": product_id,
                    "raw_material_id": rm_id,
                    "reason": "unit_row_missing",
                })
                continue

            if ing_unit["dimension"] != rm_default_unit["dimension"]:
                unconvertible.append({
                    "product_id": product_id,
                    "raw_material_id": rm_id,
                    "ingredient_unit_code": ing_unit["code"],
                    "raw_material_default_unit_code": rm_default_unit["code"],
                    "reason": "dimension_mismatch",
                })
                continue

            ing_to_base = Decimal(str(ing_unit["to_base_factor"]))
            rm_to_base = Decimal(str(rm_default_unit["to_base_factor"]))
            if rm_to_base <= 0:
                unconvertible.append({
                    "product_id": product_id,
                    "raw_material_id": rm_id,
                    "reason": "raw_material_default_unit_to_base_invalid",
                })
                continue

            qty_ing_unit = Decimal(str(ing["quantity"])) * planned_qty
            base_qty = qty_ing_unit * ing_to_base
            rm_default_qty = base_qty / rm_to_base

            rollup[rm_id] = rollup.get(rm_id, Decimal("0")) + rm_default_qty

    # Build requirements
    requirements: list[dict] = []
    total_estimated_cost = Decimal("0")
    plan_currency = "INR"
    for rm_id, required in rollup.items():
        rm = rm_map.get(rm_id)
        if rm is None:
            continue
        in_stock = await _get_current_qty_in_default_unit(
            conn,
            tenant_id=tenant_id,
            kitchen_id=kitchen_id,
            raw_material_id=rm_id,
        )
        gap = required - in_stock
        if gap < 0:
            gap = Decimal("0")

        primary = await _get_primary_supplier(
            conn, tenant_id=tenant_id, raw_material_id=rm_id,
        )
        last_known = None
        target = rm.get("target_unit_cost")
        target_dec = Decimal(str(target)) if target is not None else None
        estimated_cost = Decimal("0")
        if primary is not None:
            lk = primary.get("last_known_unit_cost")
            last_known = Decimal(str(lk)) if lk is not None else None
            unit_cost_for_est = (
                last_known
                if last_known is not None
                else (target_dec if target_dec is not None else Decimal("0"))
            )
            estimated_cost = gap * unit_cost_for_est
        elif target_dec is not None:
            estimated_cost = gap * target_dec

        currency = rm.get("currency_code") or "INR"
        plan_currency = currency
        total_estimated_cost += estimated_cost

        requirements.append({
            "raw_material_id": rm_id,
            "raw_material_name": rm.get("name"),
            "raw_material_slug": rm.get("slug"),
            "category_name": rm.get("category_name"),
            "required_qty": required,
            "required_unit_code": rm.get("default_unit_code"),
            "in_stock_qty": in_stock,
            "gap_qty": gap,
            "primary_supplier_id": primary["supplier_id"] if primary else None,
            "primary_supplier_name": primary["supplier_name"] if primary else None,
            "last_known_unit_cost": last_known,
            "target_unit_cost": target_dec,
            "estimated_cost": estimated_cost,
            "currency_code": currency,
        })

    return {
        "kitchen_id": kitchen_id,
        "horizon_start": horizon_start,
        "horizon_end": horizon_end,
        "requirements": requirements,
        "unconvertible_units": unconvertible,
        "errors": errors,
        "total_estimated_cost": total_estimated_cost,
        "currency_code": plan_currency,
    }

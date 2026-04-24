"""Recipes + nested ingredients + steps + step-equipment links repository.

Schema: "11_somaerp".
- Reads hit v_recipes, v_recipe_ingredients, v_recipe_steps, v_recipe_cost_summary.
- Writes to fct_recipes (soft-delete), dtl_recipe_ingredients (soft-delete),
  dtl_recipe_steps (soft-delete), lnk_recipe_step_equipment (hard-delete).
- Status transition to 'active' atomically archives the prior active recipe
  for the same product in the same tx.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Existence checks ────────────────────────────────────────────────────


async def product_exists(
    conn: Any, *, tenant_id: str, product_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_products "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        product_id, tenant_id,
    )
    return row is not None


async def raw_material_exists(
    conn: Any, *, tenant_id: str, material_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_raw_materials "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        material_id, tenant_id,
    )
    return row is not None


async def unit_exists(conn: Any, *, unit_id: int) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.dim_units_of_measure "
        "WHERE id = $1 AND deprecated_at IS NULL",
        unit_id,
    )
    return row is not None


async def equipment_exists(
    conn: Any, *, tenant_id: str, equipment_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_equipment "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        equipment_id, tenant_id,
    )
    return row is not None


# ── Recipes CRUD ────────────────────────────────────────────────────────


async def list_recipes(
    conn: Any,
    *,
    tenant_id: str,
    product_id: str | None = None,
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
    if product_id is not None:
        params.append(product_id)
        clauses.append(f"product_id = ${len(params)}")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        clauses.append(
            f"(COALESCE(product_name,'') ILIKE ${len(params)} "
            f"OR COALESCE(notes,'') ILIKE ${len(params)})",
        )
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_recipes "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_recipe(
    conn: Any, *, tenant_id: str, recipe_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_recipes "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        recipe_id, tenant_id,
    )
    return dict(row) if row else None


async def get_active_recipe_for_product(
    conn: Any, *, tenant_id: str, product_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id, status FROM {SCHEMA}.fct_recipes "
        "WHERE tenant_id = $1 AND product_id = $2 "
        "AND status = 'active' AND deleted_at IS NULL",
        tenant_id, product_id,
    )
    return dict(row) if row else None


async def create_recipe(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    """Create a recipe. If status='active', atomically archive any prior
    active recipe for the same product in the same tx."""
    new_id = _id.uuid7()
    status = data.get("status") or "draft"
    async with conn.transaction():
        if status == "active":
            await conn.execute(
                f"UPDATE {SCHEMA}.fct_recipes "
                "SET status = 'archived', "
                "    updated_at = CURRENT_TIMESTAMP, "
                "    updated_by = $1 "
                "WHERE tenant_id = $2 AND product_id = $3 "
                "AND status = 'active' AND deleted_at IS NULL",
                actor_user_id, tenant_id, data["product_id"],
            )
        await conn.execute(
            f"INSERT INTO {SCHEMA}.fct_recipes "
            "(id, tenant_id, product_id, version, status, effective_from, "
            " notes, properties, created_by, updated_by) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$9)",
            new_id,
            tenant_id,
            data["product_id"],
            int(data.get("version") or 1),
            status,
            data.get("effective_from"),
            data.get("notes"),
            data.get("properties") or {},
            actor_user_id,
        )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_recipes WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_RECIPE_UPDATABLE_COLUMNS = (
    "version",
    "effective_from",
    "notes",
    "properties",
)


async def update_recipe(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    recipe_id: str,
    patch: dict,
    new_status: str | None,
    existing_product_id: str,
) -> dict | None:
    """Update fields + optional status transition. If new_status='active',
    atomically archive any prior active recipe for the same product."""
    async with conn.transaction():
        # Status transition first.
        if new_status == "active":
            await conn.execute(
                f"UPDATE {SCHEMA}.fct_recipes "
                "SET status = 'archived', "
                "    updated_at = CURRENT_TIMESTAMP, "
                "    updated_by = $1 "
                "WHERE tenant_id = $2 AND product_id = $3 "
                "AND id <> $4 AND status = 'active' AND deleted_at IS NULL",
                actor_user_id, tenant_id, existing_product_id, recipe_id,
            )

        sets: list[str] = []
        params: list[Any] = []
        for col in _RECIPE_UPDATABLE_COLUMNS:
            if col in patch and patch[col] is not None:
                params.append(patch[col])
                sets.append(f"{col} = ${len(params)}")
        if new_status is not None:
            params.append(new_status)
            sets.append(f"status = ${len(params)}")

        if not sets:
            row = await conn.fetchrow(
                f"SELECT * FROM {SCHEMA}.v_recipes "
                "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
                recipe_id, tenant_id,
            )
            return dict(row) if row else None

        params.append(actor_user_id)
        sets.append(f"updated_by = ${len(params)}")
        sets.append("updated_at = CURRENT_TIMESTAMP")
        params.append(recipe_id)
        params.append(tenant_id)
        sql = (
            f"UPDATE {SCHEMA}.fct_recipes SET {', '.join(sets)} "
            f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
            "AND deleted_at IS NULL"
        )
        result = await conn.execute(sql, *params)
        if not result.endswith(" 1"):
            return None
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_recipes WHERE id = $1", recipe_id,
    )
    return dict(row) if row else None


async def soft_delete_recipe(
    conn: Any, *, tenant_id: str, actor_user_id: str, recipe_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_recipes "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, recipe_id, tenant_id,
    )
    return result.endswith(" 1")


# ── Recipe Ingredients ──────────────────────────────────────────────────


async def list_ingredients(
    conn: Any,
    *,
    tenant_id: str,
    recipe_id: str,
    include_deleted: bool = False,
) -> list[dict]:
    clauses = ["tenant_id = $1", "recipe_id = $2"]
    params: list[Any] = [tenant_id, recipe_id]
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    sql = (
        f"SELECT * FROM {SCHEMA}.v_recipe_ingredients "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY position ASC, created_at ASC"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_ingredient(
    conn: Any, *, tenant_id: str, recipe_id: str, ingredient_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_recipe_ingredients "
        "WHERE id = $1 AND tenant_id = $2 AND recipe_id = $3 "
        "AND deleted_at IS NULL",
        ingredient_id, tenant_id, recipe_id,
    )
    return dict(row) if row else None


async def create_ingredient(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    recipe_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.dtl_recipe_ingredients "
        "(id, tenant_id, recipe_id, raw_material_id, quantity, unit_id, "
        " position, notes, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$9)",
        new_id,
        tenant_id,
        recipe_id,
        data["raw_material_id"],
        data["quantity"],
        int(data["unit_id"]),
        int(data.get("position") or 1),
        data.get("notes"),
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_recipe_ingredients WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_INGREDIENT_UPDATABLE_COLUMNS = (
    "raw_material_id",
    "quantity",
    "unit_id",
    "position",
    "notes",
)


async def update_ingredient(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    recipe_id: str,
    ingredient_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _INGREDIENT_UPDATABLE_COLUMNS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_ingredient(
            conn, tenant_id=tenant_id, recipe_id=recipe_id,
            ingredient_id=ingredient_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(ingredient_id)
    params.append(tenant_id)
    params.append(recipe_id)
    sql = (
        f"UPDATE {SCHEMA}.dtl_recipe_ingredients SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 2} AND tenant_id = ${len(params) - 1} "
        f"AND recipe_id = ${len(params)} AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_ingredient(
        conn, tenant_id=tenant_id, recipe_id=recipe_id,
        ingredient_id=ingredient_id,
    )


async def soft_delete_ingredient(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    recipe_id: str,
    ingredient_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.dtl_recipe_ingredients "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND recipe_id = $4 "
        "AND deleted_at IS NULL",
        actor_user_id, ingredient_id, tenant_id, recipe_id,
    )
    return result.endswith(" 1")


# ── Recipe Steps ────────────────────────────────────────────────────────


async def list_steps(
    conn: Any,
    *,
    tenant_id: str,
    recipe_id: str,
    include_deleted: bool = False,
) -> list[dict]:
    clauses = ["tenant_id = $1", "recipe_id = $2"]
    params: list[Any] = [tenant_id, recipe_id]
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    sql = (
        f"SELECT * FROM {SCHEMA}.v_recipe_steps "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY step_number ASC"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_step(
    conn: Any, *, tenant_id: str, recipe_id: str, step_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_recipe_steps "
        "WHERE id = $1 AND tenant_id = $2 AND recipe_id = $3 "
        "AND deleted_at IS NULL",
        step_id, tenant_id, recipe_id,
    )
    return dict(row) if row else None


async def create_step(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    recipe_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.dtl_recipe_steps "
        "(id, tenant_id, recipe_id, step_number, name, duration_min, "
        " equipment_notes, instructions, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$9)",
        new_id,
        tenant_id,
        recipe_id,
        int(data["step_number"]),
        data["name"],
        data.get("duration_min"),
        data.get("equipment_notes"),
        data.get("instructions"),
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_recipe_steps WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_STEP_UPDATABLE_COLUMNS = (
    "step_number",
    "name",
    "duration_min",
    "equipment_notes",
    "instructions",
)


async def update_step(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    recipe_id: str,
    step_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _STEP_UPDATABLE_COLUMNS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_step(
            conn, tenant_id=tenant_id, recipe_id=recipe_id, step_id=step_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(step_id)
    params.append(tenant_id)
    params.append(recipe_id)
    sql = (
        f"UPDATE {SCHEMA}.dtl_recipe_steps SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 2} AND tenant_id = ${len(params) - 1} "
        f"AND recipe_id = ${len(params)} AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_step(
        conn, tenant_id=tenant_id, recipe_id=recipe_id, step_id=step_id,
    )


async def soft_delete_step(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    recipe_id: str,
    step_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.dtl_recipe_steps "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND recipe_id = $4 "
        "AND deleted_at IS NULL",
        actor_user_id, step_id, tenant_id, recipe_id,
    )
    return result.endswith(" 1")


# ── Step <-> Equipment (IMMUTABLE link) ─────────────────────────────────


async def list_step_equipment(
    conn: Any, *, tenant_id: str, step_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT lnk.id, lnk.tenant_id, lnk.step_id, lnk.equipment_id, "
        f"e.name AS equipment_name, e.slug AS equipment_slug, "
        f"c.code AS equipment_category_code, c.name AS equipment_category_name, "
        f"lnk.created_at, lnk.created_by "
        f"FROM {SCHEMA}.lnk_recipe_step_equipment lnk "
        f"LEFT JOIN {SCHEMA}.fct_equipment e ON e.id = lnk.equipment_id "
        f"LEFT JOIN {SCHEMA}.dim_equipment_categories c ON c.id = e.category_id "
        "WHERE lnk.tenant_id = $1 AND lnk.step_id = $2 "
        "ORDER BY lnk.created_at ASC",
        tenant_id, step_id,
    )
    return [dict(r) for r in rows]


async def get_step_equipment_link(
    conn: Any, *, tenant_id: str, step_id: str, equipment_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id FROM {SCHEMA}.lnk_recipe_step_equipment "
        "WHERE tenant_id = $1 AND step_id = $2 AND equipment_id = $3",
        tenant_id, step_id, equipment_id,
    )
    return dict(row) if row else None


async def create_step_equipment_link(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    step_id: str,
    equipment_id: str,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.lnk_recipe_step_equipment "
        "(id, tenant_id, step_id, equipment_id, created_by) "
        "VALUES ($1, $2, $3, $4, $5)",
        new_id, tenant_id, step_id, equipment_id, actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT id, tenant_id, step_id, equipment_id, created_at, created_by "
        f"FROM {SCHEMA}.lnk_recipe_step_equipment WHERE id = $1",
        new_id,
    )
    return dict(row) if row else {}


async def delete_step_equipment_link(
    conn: Any, *, tenant_id: str, step_id: str, equipment_id: str,
) -> bool:
    result = await conn.execute(
        f"DELETE FROM {SCHEMA}.lnk_recipe_step_equipment "
        "WHERE tenant_id = $1 AND step_id = $2 AND equipment_id = $3",
        tenant_id, step_id, equipment_id,
    )
    return result.endswith(" 1")


# ── Cost rollup ─────────────────────────────────────────────────────────


async def get_recipe_cost(
    conn: Any, *, tenant_id: str, recipe_id: str,
) -> dict | None:
    """Return RecipeCostSummary-shaped dict (with computed lines)."""
    summary = await conn.fetchrow(
        f"SELECT recipe_id, product_name, total_cost, currency_code, "
        f"ingredient_count, has_unconvertible_units "
        f"FROM {SCHEMA}.v_recipe_cost_summary "
        "WHERE recipe_id = $1 AND tenant_id = $2",
        recipe_id, tenant_id,
    )
    if summary is None:
        return None
    ing_rows = await conn.fetch(
        f"SELECT id AS ingredient_id, raw_material_id, raw_material_name, "
        f"quantity, unit_code, unit_dimension, unit_to_base_factor, "
        f"raw_material_target_unit_cost AS unit_cost, "
        f"raw_material_default_unit_dimension, "
        f"raw_material_default_to_base_factor "
        f"FROM {SCHEMA}.v_recipe_ingredients "
        "WHERE recipe_id = $1 AND tenant_id = $2 AND deleted_at IS NULL "
        "ORDER BY position ASC, created_at ASC",
        recipe_id, tenant_id,
    )
    lines: list[dict] = []
    for r in ing_rows:
        unit_cost = r["unit_cost"]
        qty = r["quantity"]
        line_cost = None
        is_unconvertible = True
        if (
            unit_cost is not None
            and r["unit_dimension"] == r["raw_material_default_unit_dimension"]
            and r["raw_material_default_to_base_factor"] is not None
            and r["raw_material_default_to_base_factor"] > 0
        ):
            line_cost = (
                qty
                * (r["unit_to_base_factor"] / r["raw_material_default_to_base_factor"])
                * unit_cost
            )
            is_unconvertible = False
        lines.append({
            "ingredient_id": r["ingredient_id"],
            "raw_material_id": r["raw_material_id"],
            "raw_material_name": r["raw_material_name"],
            "quantity": qty,
            "unit_code": r["unit_code"],
            "unit_cost": unit_cost,
            "line_cost": line_cost,
            "is_unconvertible": is_unconvertible,
        })
    out = dict(summary)
    out["lines"] = lines
    return out

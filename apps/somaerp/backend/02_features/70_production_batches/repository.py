"""Production batches repository — raw asyncpg.

Reads v_production_batches / v_batch_consumption / v_batch_step_logs /
v_batch_qc_results / v_batch_summary.

Writes fct_production_batches (soft-delete), dtl_batch_step_logs (soft-delete),
dtl_batch_ingredient_consumption (soft-delete, STORED line_cost_actual),
dtl_batch_qc_results (soft-delete). Completion side-effect also writes
evt_inventory_movements (append-only 'consumed') rows + evt_qc_checks
(append-only) in the same transaction via the qc path.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Existence checks ────────────────────────────────────────────────────


async def kitchen_exists(conn: Any, *, tenant_id: str, kitchen_id: str) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_kitchens "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        kitchen_id, tenant_id,
    )
    return row is not None


async def product_exists(conn: Any, *, tenant_id: str, product_id: str) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_products "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        product_id, tenant_id,
    )
    return row is not None


async def get_product(conn: Any, *, tenant_id: str, product_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id, currency_code, default_selling_price, name "
        f"FROM {SCHEMA}.fct_products "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        product_id, tenant_id,
    )
    return dict(row) if row else None


async def get_active_recipe_for_product(
    conn: Any, *, tenant_id: str, product_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id, version, status FROM {SCHEMA}.fct_recipes "
        "WHERE product_id = $1 AND tenant_id = $2 "
        "AND status = 'active' AND deleted_at IS NULL "
        "ORDER BY version DESC LIMIT 1",
        product_id, tenant_id,
    )
    return dict(row) if row else None


async def get_recipe(
    conn: Any, *, tenant_id: str, recipe_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id, product_id, version, status FROM {SCHEMA}.fct_recipes "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        recipe_id, tenant_id,
    )
    return dict(row) if row else None


async def checkpoint_exists(
    conn: Any, *, tenant_id: str, checkpoint_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.dim_qc_checkpoints "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        checkpoint_id, tenant_id,
    )
    return row is not None


async def outcome_exists(conn: Any, *, outcome_id: int) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.dim_qc_outcomes "
        "WHERE id = $1 AND deprecated_at IS NULL",
        outcome_id,
    )
    return row is not None


# ── Batch list/get ──────────────────────────────────────────────────────


async def list_batches(
    conn: Any,
    *,
    tenant_id: str,
    kitchen_id: str | None = None,
    product_id: str | None = None,
    recipe_id: str | None = None,
    status: str | None = None,
    run_date_from: date | None = None,
    run_date_to: date | None = None,
    lead_user_id: str | None = None,
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
    if product_id is not None:
        params.append(product_id)
        clauses.append(f"product_id = ${len(params)}")
    if recipe_id is not None:
        params.append(recipe_id)
        clauses.append(f"recipe_id = ${len(params)}")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if run_date_from is not None:
        params.append(run_date_from)
        clauses.append(f"run_date >= ${len(params)}")
    if run_date_to is not None:
        params.append(run_date_to)
        clauses.append(f"run_date <= ${len(params)}")
    if lead_user_id is not None:
        params.append(lead_user_id)
        clauses.append(f"lead_user_id = ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_production_batches "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY run_date DESC, created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_batch(
    conn: Any, *, tenant_id: str, batch_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_production_batches "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        batch_id, tenant_id,
    )
    return dict(row) if row else None


async def get_batch_summary(
    conn: Any, *, tenant_id: str, batch_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_batch_summary "
        "WHERE batch_id = $1 AND tenant_id = $2",
        batch_id, tenant_id,
    )
    return dict(row) if row else None


# ── Batch create (atomic transaction) ───────────────────────────────────


async def create_batch(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> tuple[dict, dict]:
    """Create a planned batch. Returns (batch_row, recipe_row).

    Atomically:
      1. Resolve recipe (use provided or pick active for product).
      2. Insert fct_production_batches (status=planned).
      3. From fct_recipes steps: insert dtl_batch_step_logs per step.
      4. From dtl_recipe_ingredients: insert dtl_batch_ingredient_consumption
         with planned_qty = ingredient.qty * planned_qty * unit_conversion_factor,
         actual_qty NULL, unit_cost_snapshot from raw_material.target_unit_cost.
    """
    new_id = _id.uuid7()
    planned_qty = Decimal(str(data["planned_qty"]))
    currency_code = data["currency_code"]
    run_date_val = data.get("run_date") or date.today()
    shift_start_val = data.get("shift_start")

    recipe_row: dict = data["recipe_row"]

    async with conn.transaction():
        await conn.execute(
            f"INSERT INTO {SCHEMA}.fct_production_batches "
            "(id, tenant_id, kitchen_id, product_id, recipe_id, run_date, "
            " planned_qty, actual_qty, status, shift_start, currency_code, "
            " lead_user_id, notes, properties, created_by, updated_by) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,NULL,'planned',$8,$9,$10,$11,$12,$13,$13)",
            new_id,
            tenant_id,
            data["kitchen_id"],
            data["product_id"],
            recipe_row["id"],
            run_date_val,
            planned_qty,
            shift_start_val,
            currency_code,
            data.get("lead_user_id"),
            data.get("notes"),
            data.get("properties") or {},
            actor_user_id,
        )

        # Pull recipe steps in order.
        step_rows = await conn.fetch(
            f"SELECT id, step_number, name FROM {SCHEMA}.dtl_recipe_steps "
            "WHERE recipe_id = $1 AND tenant_id = $2 AND deleted_at IS NULL "
            "ORDER BY step_number ASC",
            recipe_row["id"], tenant_id,
        )
        for sr in step_rows:
            log_id = _id.uuid7()
            await conn.execute(
                f"INSERT INTO {SCHEMA}.dtl_batch_step_logs "
                "(id, tenant_id, batch_id, recipe_step_id, step_number, "
                " name, created_by, updated_by) "
                "VALUES ($1,$2,$3,$4,$5,$6,$7,$7)",
                log_id,
                tenant_id,
                new_id,
                sr["id"],
                int(sr["step_number"]),
                sr["name"],
                actor_user_id,
            )

        # Pull recipe ingredients + unit + raw_material cost info.
        ing_rows = await conn.fetch(
            f"SELECT i.id AS ingredient_id, i.raw_material_id, i.quantity, "
            f"       i.unit_id AS ingredient_unit_id, "
            f"       u_ing.dimension AS ingredient_dim, "
            f"       u_ing.to_base_factor AS ingredient_to_base, "
            f"       rm.default_unit_id AS rm_default_unit_id, "
            f"       u_rm.dimension AS rm_dim, "
            f"       u_rm.to_base_factor AS rm_to_base, "
            f"       rm.target_unit_cost, rm.currency_code AS rm_currency_code "
            f"FROM {SCHEMA}.dtl_recipe_ingredients i "
            f"JOIN {SCHEMA}.fct_raw_materials rm ON rm.id = i.raw_material_id "
            f"JOIN {SCHEMA}.dim_units_of_measure u_ing ON u_ing.id = i.unit_id "
            f"JOIN {SCHEMA}.dim_units_of_measure u_rm ON u_rm.id = rm.default_unit_id "
            f"WHERE i.recipe_id = $1 AND i.tenant_id = $2 AND i.deleted_at IS NULL "
            f"ORDER BY i.position ASC",
            recipe_row["id"], tenant_id,
        )
        for ir in ing_rows:
            ir_quantity = Decimal(str(ir["quantity"]))
            ing_to_base = ir["ingredient_to_base"]
            rm_to_base = ir["rm_to_base"]
            if (
                ir["ingredient_dim"] == ir["rm_dim"]
                and ing_to_base is not None
                and rm_to_base is not None
                and Decimal(str(rm_to_base)) > 0
            ):
                conv = Decimal(str(ing_to_base)) / Decimal(str(rm_to_base))
            else:
                conv = Decimal("1")
            planned_line_qty = ir_quantity * planned_qty * conv
            unit_cost = (
                Decimal(str(ir["target_unit_cost"]))
                if ir["target_unit_cost"] is not None
                else Decimal("0")
            )
            line_currency = ir["rm_currency_code"] or currency_code
            cons_id = _id.uuid7()
            await conn.execute(
                f"INSERT INTO {SCHEMA}.dtl_batch_ingredient_consumption "
                "(id, tenant_id, batch_id, raw_material_id, recipe_ingredient_id, "
                " planned_qty, actual_qty, unit_id, unit_cost_snapshot, "
                " currency_code, lot_number, created_by, updated_by) "
                "VALUES ($1,$2,$3,$4,$5,$6,NULL,$7,$8,$9,NULL,$10,$10)",
                cons_id,
                tenant_id,
                new_id,
                ir["raw_material_id"],
                ir["ingredient_id"],
                planned_line_qty,
                int(ir["rm_default_unit_id"]),
                unit_cost,
                line_currency,
                actor_user_id,
            )

    row = await get_batch(conn, tenant_id=tenant_id, batch_id=new_id)
    return (row or {}, recipe_row)


# ── Batch update (state machine + field patches) ────────────────────────


_BATCH_UPDATABLE_COLUMNS = ("notes", "lead_user_id", "properties", "cancel_reason")


async def _insert_consumption_movements(
    conn: Any,
    *,
    tenant_id: str,
    batch_id: str,
    kitchen_id: str,
    actor_user_id: str,
) -> int:
    """For each consumption line with actual_qty > 0, insert a consumed
    inventory movement. Returns the number of movements inserted."""
    rows = await conn.fetch(
        f"SELECT id, raw_material_id, actual_qty, unit_id, lot_number "
        f"FROM {SCHEMA}.dtl_batch_ingredient_consumption "
        f"WHERE batch_id = $1 AND tenant_id = $2 AND deleted_at IS NULL "
        f"AND actual_qty IS NOT NULL AND actual_qty > 0",
        batch_id, tenant_id,
    )
    count = 0
    for r in rows:
        mv_id = _id.uuid7()
        await conn.execute(
            f"INSERT INTO {SCHEMA}.evt_inventory_movements "
            "(id, tenant_id, kitchen_id, raw_material_id, movement_type, "
            " quantity, unit_id, lot_number, batch_id_ref, procurement_run_id, "
            " reason, performed_by_user_id, metadata) "
            "VALUES ($1,$2,$3,$4,'consumed',$5,$6,$7,$8,NULL,$9,$10,$11)",
            mv_id,
            tenant_id,
            kitchen_id,
            r["raw_material_id"],
            Decimal(str(r["actual_qty"])),
            int(r["unit_id"]),
            r["lot_number"],
            batch_id,
            f"batch_{batch_id}_completed",
            actor_user_id,
            {
                "source": "batch_completion",
                "batch_id": batch_id,
                "consumption_line_id": r["id"],
            },
        )
        count += 1
    return count


async def _default_missing_actuals(
    conn: Any, *, tenant_id: str, batch_id: str, actor_user_id: str,
) -> int:
    """For consumption lines where actual_qty is still NULL, copy planned_qty
    into actual_qty so the 'consumed' movement line reflects the plan.
    Returns number of rows defaulted."""
    result = await conn.execute(
        f"UPDATE {SCHEMA}.dtl_batch_ingredient_consumption "
        "SET actual_qty = planned_qty, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE batch_id = $2 AND tenant_id = $3 "
        "AND actual_qty IS NULL AND deleted_at IS NULL",
        actor_user_id, batch_id, tenant_id,
    )
    # asyncpg returns e.g. "UPDATE 3"
    try:
        return int(result.rsplit(" ", 1)[1])
    except Exception:
        return 0


async def patch_batch(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    existing: dict,
    patch: dict,
) -> tuple[dict, str, int]:
    """Apply status transition + optional field patches.
    Returns (updated_batch_row, event_kind, movements_inserted).
    event_kind is one of: 'updated' | 'started' | 'completed' | 'cancelled'.
    """
    new_status = patch.get("status")
    old_status = existing["status"]
    event_kind = "updated"
    movements = 0

    set_parts: list[str] = []
    params: list[Any] = []

    if new_status is not None and new_status != old_status:
        # Validate transitions.
        allowed = {
            "planned": {"in_progress", "cancelled"},
            "in_progress": {"completed", "cancelled"},
            "completed": set(),
            "cancelled": set(),
        }
        if new_status not in allowed.get(old_status, set()):
            from importlib import import_module as _im
            _err = _im("apps.somaerp.backend.01_core.errors")
            raise _err.ValidationError(
                f"Invalid status transition {old_status} -> {new_status}.",
                code="INVALID_STATUS_TRANSITION",
            )

        if new_status == "in_progress":
            event_kind = "started"
            params.append(new_status)
            set_parts.append(f"status = ${len(params)}")
            # shift_start = now if not provided earlier
            params.append(datetime.utcnow())
            set_parts.append(f"shift_start = COALESCE(shift_start, ${len(params)})")
        elif new_status == "completed":
            # Require actual_qty (from patch or existing).
            actual_qty = patch.get("actual_qty")
            if actual_qty is None and existing.get("actual_qty") is None:
                from importlib import import_module as _im
                _err = _im("apps.somaerp.backend.01_core.errors")
                raise _err.ValidationError(
                    "actual_qty is required to complete a batch.",
                    code="MISSING_ACTUAL_QTY",
                )
            event_kind = "completed"
            params.append(new_status)
            set_parts.append(f"status = ${len(params)}")
            if actual_qty is not None:
                params.append(Decimal(str(actual_qty)))
                set_parts.append(f"actual_qty = ${len(params)}")
            # shift_end = now
            params.append(datetime.utcnow())
            set_parts.append(f"shift_end = ${len(params)}")
        elif new_status == "cancelled":
            event_kind = "cancelled"
            params.append(new_status)
            set_parts.append(f"status = ${len(params)}")
            if patch.get("cancel_reason") is not None:
                params.append(patch["cancel_reason"])
                set_parts.append(f"cancel_reason = ${len(params)}")
            params.append(datetime.utcnow())
            set_parts.append(f"shift_end = COALESCE(shift_end, ${len(params)})")

    # Non-status field patches are allowed any time except after completion.
    if old_status != "completed":
        for col in _BATCH_UPDATABLE_COLUMNS:
            if col == "cancel_reason" and new_status == "cancelled":
                # already handled above
                continue
            if col in patch and patch[col] is not None:
                params.append(patch[col])
                set_parts.append(f"{col} = ${len(params)}")
        # actual_qty may be patched (planned->in_progress flow allows early setting)
        if (
            new_status is None
            and "actual_qty" in patch
            and patch["actual_qty"] is not None
            and old_status in ("planned", "in_progress")
        ):
            params.append(Decimal(str(patch["actual_qty"])))
            set_parts.append(f"actual_qty = ${len(params)}")

    async with conn.transaction():
        if event_kind == "completed":
            # Default any NULL consumption actuals to planned.
            await _default_missing_actuals(
                conn,
                tenant_id=tenant_id,
                batch_id=existing["id"],
                actor_user_id=actor_user_id,
            )

        if set_parts:
            params.append(actor_user_id)
            set_parts.append(f"updated_by = ${len(params)}")
            set_parts.append("updated_at = CURRENT_TIMESTAMP")
            params.append(existing["id"])
            params.append(tenant_id)
            sql = (
                f"UPDATE {SCHEMA}.fct_production_batches SET "
                f"{', '.join(set_parts)} "
                f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
                "AND deleted_at IS NULL"
            )
            await conn.execute(sql, *params)

        if event_kind == "completed":
            movements = await _insert_consumption_movements(
                conn,
                tenant_id=tenant_id,
                batch_id=existing["id"],
                kitchen_id=existing["kitchen_id"],
                actor_user_id=actor_user_id,
            )

    row = await get_batch(conn, tenant_id=tenant_id, batch_id=existing["id"])
    return (row or {}, event_kind, movements)


async def soft_delete_batch(
    conn: Any, *, tenant_id: str, actor_user_id: str, batch_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_production_batches "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, batch_id, tenant_id,
    )
    return result.endswith(" 1")


# ── Step logs ──────────────────────────────────────────────────────────


async def list_batch_steps(
    conn: Any, *, tenant_id: str, batch_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {SCHEMA}.v_batch_step_logs "
        "WHERE batch_id = $1 AND tenant_id = $2 AND deleted_at IS NULL "
        "ORDER BY step_number ASC",
        batch_id, tenant_id,
    )
    return [dict(r) for r in rows]


async def get_step(
    conn: Any, *, tenant_id: str, batch_id: str, step_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_batch_step_logs "
        "WHERE id = $1 AND batch_id = $2 AND tenant_id = $3 "
        "AND deleted_at IS NULL",
        step_id, batch_id, tenant_id,
    )
    return dict(row) if row else None


async def patch_step(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    batch_id: str,
    step_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in ("started_at", "completed_at", "notes"):
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if "started_at" in patch or "completed_at" in patch:
        params.append(actor_user_id)
        sets.append(f"performed_by_user_id = COALESCE(performed_by_user_id, ${len(params)})")
    if not sets:
        return await get_step(
            conn, tenant_id=tenant_id, batch_id=batch_id, step_id=step_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(step_id)
    params.append(batch_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.dtl_batch_step_logs SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 2} AND batch_id = ${len(params) - 1} "
        f"AND tenant_id = ${len(params)} AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_step(
        conn, tenant_id=tenant_id, batch_id=batch_id, step_id=step_id,
    )


# ── Consumption ────────────────────────────────────────────────────────


async def list_batch_consumption(
    conn: Any, *, tenant_id: str, batch_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {SCHEMA}.v_batch_consumption "
        "WHERE batch_id = $1 AND tenant_id = $2 AND deleted_at IS NULL "
        "ORDER BY created_at ASC",
        batch_id, tenant_id,
    )
    return [dict(r) for r in rows]


async def get_consumption_line(
    conn: Any, *, tenant_id: str, batch_id: str, line_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_batch_consumption "
        "WHERE id = $1 AND batch_id = $2 AND tenant_id = $3 "
        "AND deleted_at IS NULL",
        line_id, batch_id, tenant_id,
    )
    return dict(row) if row else None


async def patch_consumption(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    batch_id: str,
    line_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in ("actual_qty", "lot_number", "unit_cost_snapshot"):
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_consumption_line(
            conn, tenant_id=tenant_id, batch_id=batch_id, line_id=line_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(line_id)
    params.append(batch_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.dtl_batch_ingredient_consumption "
        f"SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 2} AND batch_id = ${len(params) - 1} "
        f"AND tenant_id = ${len(params)} AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_consumption_line(
        conn, tenant_id=tenant_id, batch_id=batch_id, line_id=line_id,
    )


# ── QC results ──────────────────────────────────────────────────────────


async def list_batch_qc_results(
    conn: Any, *, tenant_id: str, batch_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {SCHEMA}.v_batch_qc_results "
        "WHERE batch_id = $1 AND tenant_id = $2 AND deleted_at IS NULL "
        "ORDER BY created_at DESC",
        batch_id, tenant_id,
    )
    return [dict(r) for r in rows]


async def record_batch_qc(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    batch: dict,
    data: dict,
) -> tuple[dict, str]:
    """Insert evt_qc_checks + upsert dtl_batch_qc_results rollup row.
    Returns (qc_row_dict, event_id).
    """
    event_id = _id.uuid7()
    async with conn.transaction():
        await conn.execute(
            f"INSERT INTO {SCHEMA}.evt_qc_checks "
            "(id, tenant_id, checkpoint_id, batch_id, kitchen_id, "
            " outcome_id, measured_value, measured_unit_id, notes, "
            " photo_vault_key, performed_by_user_id, metadata) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)",
            event_id,
            tenant_id,
            data["checkpoint_id"],
            batch["id"],
            batch["kitchen_id"],
            int(data["outcome_id"]),
            data.get("measured_value"),
            int(data["measured_unit_id"]) if data.get("measured_unit_id") is not None else None,
            data.get("notes"),
            data.get("photo_vault_key"),
            actor_user_id,
            data.get("metadata") or {},
        )

        # Upsert summary rollup: if row exists, update; else insert.
        existing = await conn.fetchrow(
            f"SELECT id, events_count FROM {SCHEMA}.dtl_batch_qc_results "
            "WHERE batch_id = $1 AND checkpoint_id = $2 AND tenant_id = $3 "
            "AND deleted_at IS NULL",
            batch["id"], data["checkpoint_id"], tenant_id,
        )
        if existing is None:
            roll_id = _id.uuid7()
            await conn.execute(
                f"INSERT INTO {SCHEMA}.dtl_batch_qc_results "
                "(id, tenant_id, batch_id, checkpoint_id, outcome_id, "
                " measured_value, measured_unit_id, notes, photo_vault_key, "
                " performed_by_user_id, last_event_id, events_count, "
                " created_by, updated_by) "
                "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,1,$12,$12)",
                roll_id,
                tenant_id,
                batch["id"],
                data["checkpoint_id"],
                int(data["outcome_id"]),
                data.get("measured_value"),
                int(data["measured_unit_id"]) if data.get("measured_unit_id") is not None else None,
                data.get("notes"),
                data.get("photo_vault_key"),
                actor_user_id,
                actor_user_id,
            )
        else:
            await conn.execute(
                f"UPDATE {SCHEMA}.dtl_batch_qc_results "
                "SET outcome_id = $1, measured_value = $2, measured_unit_id = $3, "
                "    notes = $4, photo_vault_key = $5, performed_by_user_id = $6, "
                "    last_event_id = $7, events_count = events_count + 1, "
                "    updated_at = CURRENT_TIMESTAMP, updated_by = $8 "
                "WHERE id = $9 AND tenant_id = $10",
                int(data["outcome_id"]),
                data.get("measured_value"),
                int(data["measured_unit_id"]) if data.get("measured_unit_id") is not None else None,
                data.get("notes"),
                data.get("photo_vault_key"),
                actor_user_id,
                actor_user_id,
                existing["id"],
                tenant_id,
            )

    # Read back the rollup row.
    roll = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_batch_qc_results "
        "WHERE batch_id = $1 AND checkpoint_id = $2 AND tenant_id = $3 "
        "AND deleted_at IS NULL",
        batch["id"], data["checkpoint_id"], tenant_id,
    )
    return (dict(roll) if roll else {}, event_id)

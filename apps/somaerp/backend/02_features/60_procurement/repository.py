"""Procurement runs + lines repository — raw asyncpg.

Schema: "11_somaerp".
- Reads run list/get from v_procurement_runs; lines from joined v-like SELECT.
- Writes to fct_procurement_runs (soft-delete), dtl_procurement_lines (soft-delete).
- Line create/update/delete also writes to evt_inventory_movements in the same tx.
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


async def supplier_exists(
    conn: Any, *, tenant_id: str, supplier_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_suppliers "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        supplier_id, tenant_id,
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


# ── Runs CRUD ───────────────────────────────────────────────────────────


async def list_runs(
    conn: Any,
    *,
    tenant_id: str,
    kitchen_id: str | None = None,
    supplier_id: str | None = None,
    status: str | None = None,
    run_date_from: date | None = None,
    run_date_to: date | None = None,
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
    if supplier_id is not None:
        params.append(supplier_id)
        clauses.append(f"supplier_id = ${len(params)}")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if run_date_from is not None:
        params.append(run_date_from)
        clauses.append(f"run_date >= ${len(params)}")
    if run_date_to is not None:
        params.append(run_date_to)
        clauses.append(f"run_date <= ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_procurement_runs "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY run_date DESC, created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_run(
    conn: Any, *, tenant_id: str, run_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_procurement_runs "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        run_id, tenant_id,
    )
    return dict(row) if row else None


async def create_run(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_procurement_runs "
        "(id, tenant_id, kitchen_id, supplier_id, run_date, "
        " performed_by_user_id, total_cost, currency_code, notes, "
        " status, properties, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,0,$7,$8,'active',$9,$10,$10)",
        new_id,
        tenant_id,
        data["kitchen_id"],
        data["supplier_id"],
        data["run_date"],
        actor_user_id,
        data["currency_code"],
        data.get("notes"),
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_procurement_runs WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_RUN_UPDATABLE_COLUMNS = ("notes", "properties", "status")


async def update_run(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    run_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _RUN_UPDATABLE_COLUMNS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_run(conn, tenant_id=tenant_id, run_id=run_id)
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(run_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.fct_procurement_runs SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_run(conn, tenant_id=tenant_id, run_id=run_id)


async def soft_delete_run(
    conn: Any, *, tenant_id: str, actor_user_id: str, run_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_procurement_runs "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, run_id, tenant_id,
    )
    return result.endswith(" 1")


# ── Lines CRUD ──────────────────────────────────────────────────────────


_LINE_SELECT = (
    f"SELECT l.id, l.tenant_id, l.procurement_run_id, l.raw_material_id, "
    f"rm.name AS raw_material_name, rm.slug AS raw_material_slug, "
    f"l.quantity, l.unit_id, u.code AS unit_code, "
    f"l.unit_cost, l.line_cost, l.lot_number, l.quality_grade, "
    f"l.received_at, l.created_at, l.updated_at, l.created_by, "
    f"l.updated_by, l.deleted_at "
    f"FROM {SCHEMA}.dtl_procurement_lines l "
    f"LEFT JOIN {SCHEMA}.fct_raw_materials rm ON rm.id = l.raw_material_id "
    f"LEFT JOIN {SCHEMA}.dim_units_of_measure u ON u.id = l.unit_id "
)


async def list_lines(
    conn: Any,
    *,
    tenant_id: str,
    run_id: str,
    include_deleted: bool = False,
) -> list[dict]:
    clauses = ["l.tenant_id = $1", "l.procurement_run_id = $2"]
    params: list[Any] = [tenant_id, run_id]
    if not include_deleted:
        clauses.append("l.deleted_at IS NULL")
    sql = (
        f"{_LINE_SELECT}WHERE {' AND '.join(clauses)} "
        f"ORDER BY l.created_at ASC"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_line(
    conn: Any, *, tenant_id: str, run_id: str, line_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"{_LINE_SELECT}"
        "WHERE l.id = $1 AND l.tenant_id = $2 "
        "AND l.procurement_run_id = $3 AND l.deleted_at IS NULL",
        line_id, tenant_id, run_id,
    )
    return dict(row) if row else None


async def _refresh_run_total(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    run_id: str,
) -> None:
    await conn.execute(
        f"UPDATE {SCHEMA}.fct_procurement_runs "
        "SET total_cost = COALESCE("
        f"    (SELECT SUM(line_cost) FROM {SCHEMA}.dtl_procurement_lines "
        "      WHERE procurement_run_id = $1 AND tenant_id = $2 "
        "      AND deleted_at IS NULL), 0"
        "   ), "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $3 "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        run_id, tenant_id, actor_user_id,
    )


async def _insert_movement(
    conn: Any,
    *,
    tenant_id: str,
    kitchen_id: str,
    raw_material_id: str,
    movement_type: str,
    quantity: Decimal,
    unit_id: int,
    lot_number: str | None,
    procurement_run_id: str | None,
    reason: str | None,
    performed_by_user_id: str,
    metadata: dict | None = None,
) -> str:
    mv_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.evt_inventory_movements "
        "(id, tenant_id, kitchen_id, raw_material_id, movement_type, "
        " quantity, unit_id, lot_number, batch_id_ref, procurement_run_id, "
        " reason, performed_by_user_id, metadata) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,NULL,$9,$10,$11,$12)",
        mv_id,
        tenant_id,
        kitchen_id,
        raw_material_id,
        movement_type,
        quantity,
        int(unit_id),
        lot_number,
        procurement_run_id,
        reason,
        performed_by_user_id,
        metadata or {},
    )
    return mv_id


async def add_line(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    run: dict,
    data: dict,
) -> tuple[dict, str]:
    """Insert a line + a 'received' inventory movement + refresh run total.
    Returns (line_row, movement_id)."""
    new_id = _id.uuid7()
    movement_id: str = ""
    async with conn.transaction():
        await conn.execute(
            f"INSERT INTO {SCHEMA}.dtl_procurement_lines "
            "(id, tenant_id, procurement_run_id, raw_material_id, "
            " quantity, unit_id, unit_cost, lot_number, quality_grade, "
            " received_at, created_by, updated_by) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$11)",
            new_id,
            tenant_id,
            run["id"],
            data["raw_material_id"],
            data["quantity"],
            int(data["unit_id"]),
            data["unit_cost"],
            data.get("lot_number"),
            data.get("quality_grade"),
            data.get("received_at"),
            actor_user_id,
        )
        movement_id = await _insert_movement(
            conn,
            tenant_id=tenant_id,
            kitchen_id=run["kitchen_id"],
            raw_material_id=data["raw_material_id"],
            movement_type="received",
            quantity=data["quantity"],
            unit_id=int(data["unit_id"]),
            lot_number=data.get("lot_number"),
            procurement_run_id=run["id"],
            reason=None,
            performed_by_user_id=actor_user_id,
            metadata={"source": "procurement_line", "line_id": new_id},
        )
        await _refresh_run_total(
            conn,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            run_id=run["id"],
        )
    row = await get_line(
        conn, tenant_id=tenant_id, run_id=run["id"], line_id=new_id,
    )
    return (row or {}, movement_id)


_LINE_UPDATABLE_COLUMNS = (
    "quantity",
    "unit_id",
    "unit_cost",
    "lot_number",
    "quality_grade",
    "received_at",
)


async def patch_line(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    run: dict,
    existing_line: dict,
    patch: dict,
) -> dict | None:
    """Update line fields. If quantity changed, emit a compensating
    'adjusted' movement for (new_qty - old_qty) in the line's unit:
      - positive delta → 'adjusted' with positive qty  (adds to stock)
      - negative delta → 'adjusted' with abs(delta) qty + reason=compensating
        (evt constraint says qty > 0, adjusted always treated as POSITIVE
        add in v_inventory_current; for negative delta we issue a 'consumed'
        compensating movement instead to avoid inflating stock)
    """
    sets: list[str] = []
    params: list[Any] = []
    for col in _LINE_UPDATABLE_COLUMNS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")

    async with conn.transaction():
        if sets:
            params.append(actor_user_id)
            sets.append(f"updated_by = ${len(params)}")
            sets.append("updated_at = CURRENT_TIMESTAMP")
            params.append(existing_line["id"])
            params.append(tenant_id)
            params.append(run["id"])
            sql = (
                f"UPDATE {SCHEMA}.dtl_procurement_lines SET {', '.join(sets)} "
                f"WHERE id = ${len(params) - 2} AND tenant_id = ${len(params) - 1} "
                f"AND procurement_run_id = ${len(params)} AND deleted_at IS NULL"
            )
            result = await conn.execute(sql, *params)
            if not result.endswith(" 1"):
                return None

        new_qty = patch.get("quantity")
        if new_qty is not None:
            old_qty = Decimal(str(existing_line["quantity"]))
            new_qty_dec = Decimal(str(new_qty))
            delta = new_qty_dec - old_qty
            if delta != 0:
                if delta > 0:
                    await _insert_movement(
                        conn,
                        tenant_id=tenant_id,
                        kitchen_id=run["kitchen_id"],
                        raw_material_id=existing_line["raw_material_id"],
                        movement_type="adjusted",
                        quantity=delta,
                        unit_id=int(
                            patch.get("unit_id") or existing_line["unit_id"]
                        ),
                        lot_number=patch.get("lot_number") or existing_line.get("lot_number"),
                        procurement_run_id=run["id"],
                        reason="procurement_line_quantity_increase",
                        performed_by_user_id=actor_user_id,
                        metadata={
                            "source": "procurement_line_patch",
                            "line_id": existing_line["id"],
                            "old_quantity": str(old_qty),
                            "new_quantity": str(new_qty_dec),
                        },
                    )
                else:
                    # Negative delta → compensating 'consumed' row
                    await _insert_movement(
                        conn,
                        tenant_id=tenant_id,
                        kitchen_id=run["kitchen_id"],
                        raw_material_id=existing_line["raw_material_id"],
                        movement_type="consumed",
                        quantity=-delta,
                        unit_id=int(
                            patch.get("unit_id") or existing_line["unit_id"]
                        ),
                        lot_number=patch.get("lot_number") or existing_line.get("lot_number"),
                        procurement_run_id=run["id"],
                        reason="procurement_line_quantity_decrease",
                        performed_by_user_id=actor_user_id,
                        metadata={
                            "source": "procurement_line_patch",
                            "line_id": existing_line["id"],
                            "old_quantity": str(old_qty),
                            "new_quantity": str(new_qty_dec),
                        },
                    )
            await _refresh_run_total(
                conn,
                tenant_id=tenant_id,
                actor_user_id=actor_user_id,
                run_id=run["id"],
            )

    return await get_line(
        conn,
        tenant_id=tenant_id,
        run_id=run["id"],
        line_id=existing_line["id"],
    )


async def soft_delete_line(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    run: dict,
    existing_line: dict,
) -> bool:
    async with conn.transaction():
        result = await conn.execute(
            f"UPDATE {SCHEMA}.dtl_procurement_lines "
            "SET deleted_at = CURRENT_TIMESTAMP, "
            "    updated_at = CURRENT_TIMESTAMP, "
            "    updated_by = $1 "
            "WHERE id = $2 AND tenant_id = $3 "
            "AND procurement_run_id = $4 AND deleted_at IS NULL",
            actor_user_id,
            existing_line["id"],
            tenant_id,
            run["id"],
        )
        if not result.endswith(" 1"):
            return False
        # Compensating 'consumed' movement of full line quantity.
        await _insert_movement(
            conn,
            tenant_id=tenant_id,
            kitchen_id=run["kitchen_id"],
            raw_material_id=existing_line["raw_material_id"],
            movement_type="consumed",
            quantity=Decimal(str(existing_line["quantity"])),
            unit_id=int(existing_line["unit_id"]),
            lot_number=existing_line.get("lot_number"),
            procurement_run_id=run["id"],
            reason="procurement_line_deleted",
            performed_by_user_id=actor_user_id,
            metadata={
                "source": "procurement_line_delete",
                "line_id": existing_line["id"],
            },
        )
        await _refresh_run_total(
            conn,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            run_id=run["id"],
        )
    return True

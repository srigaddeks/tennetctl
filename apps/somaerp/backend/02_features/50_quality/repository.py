"""Quality repository — raw asyncpg.

Schema: "11_somaerp".
- Reads hit v_qc_checkpoints + v_qc_checks.
- Writes to dim_qc_checkpoints (soft-delete) and evt_qc_checks (append-only).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Lookups (read-only) ────────────────────────────────────────────────


async def list_check_types(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT id, code, name, deprecated_at "
        f"FROM {SCHEMA}.dim_qc_check_types "
        "WHERE deprecated_at IS NULL "
        "ORDER BY id ASC"
    )
    return [dict(r) for r in rows]


async def check_type_exists(conn: Any, *, check_type_id: int) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.dim_qc_check_types "
        "WHERE id = $1 AND deprecated_at IS NULL",
        check_type_id,
    )
    return row is not None


async def list_stages(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT id, code, name, deprecated_at "
        f"FROM {SCHEMA}.dim_qc_stages "
        "WHERE deprecated_at IS NULL "
        "ORDER BY id ASC"
    )
    return [dict(r) for r in rows]


async def stage_exists(conn: Any, *, stage_id: int) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.dim_qc_stages "
        "WHERE id = $1 AND deprecated_at IS NULL",
        stage_id,
    )
    return row is not None


async def list_outcomes(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT id, code, name, deprecated_at "
        f"FROM {SCHEMA}.dim_qc_outcomes "
        "WHERE deprecated_at IS NULL "
        "ORDER BY id ASC"
    )
    return [dict(r) for r in rows]


async def outcome_exists(conn: Any, *, outcome_id: int) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.dim_qc_outcomes "
        "WHERE id = $1 AND deprecated_at IS NULL",
        outcome_id,
    )
    return row is not None


# ── Scope-ref existence checks (per scope_kind) ────────────────────────


async def recipe_step_exists_for_tenant(
    conn: Any, *, tenant_id: str, step_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.dtl_recipe_steps "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        step_id, tenant_id,
    )
    return row is not None


async def raw_material_exists_for_tenant(
    conn: Any, *, tenant_id: str, raw_material_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_raw_materials "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        raw_material_id, tenant_id,
    )
    return row is not None


async def kitchen_exists_for_tenant(
    conn: Any, *, tenant_id: str, kitchen_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_kitchens "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        kitchen_id, tenant_id,
    )
    return row is not None


async def product_exists_for_tenant(
    conn: Any, *, tenant_id: str, product_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_products "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        product_id, tenant_id,
    )
    return row is not None


# ── Checkpoints CRUD ───────────────────────────────────────────────────


async def list_checkpoints(
    conn: Any,
    *,
    tenant_id: str,
    scope_kind: str | None = None,
    scope_ref_id: str | None = None,
    stage_id: int | None = None,
    check_type_id: int | None = None,
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
    if scope_kind is not None:
        params.append(scope_kind)
        clauses.append(f"scope_kind = ${len(params)}")
    if scope_ref_id is not None:
        params.append(scope_ref_id)
        clauses.append(f"scope_ref_id = ${len(params)}")
    if stage_id is not None:
        params.append(stage_id)
        clauses.append(f"stage_id = ${len(params)}")
    if check_type_id is not None:
        params.append(check_type_id)
        clauses.append(f"check_type_id = ${len(params)}")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        clauses.append(f"name ILIKE ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_qc_checkpoints "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_checkpoint(
    conn: Any, *, tenant_id: str, checkpoint_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_qc_checkpoints "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        checkpoint_id, tenant_id,
    )
    return dict(row) if row else None


async def create_checkpoint(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.dim_qc_checkpoints "
        "(id, tenant_id, stage_id, check_type_id, scope_kind, scope_ref_id, "
        " name, criteria_jsonb, required, status, properties, "
        " created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$12)",
        new_id,
        tenant_id,
        int(data["stage_id"]),
        int(data["check_type_id"]),
        data["scope_kind"],
        data.get("scope_ref_id"),
        data["name"],
        data.get("criteria_jsonb") or {},
        bool(data.get("required", True)),
        data.get("status") or "active",
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_qc_checkpoints WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_CHECKPOINT_UPDATABLE_COLUMNS = (
    "stage_id",
    "check_type_id",
    "scope_kind",
    "scope_ref_id",
    "name",
    "criteria_jsonb",
    "required",
    "status",
    "properties",
)


async def update_checkpoint(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    checkpoint_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _CHECKPOINT_UPDATABLE_COLUMNS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_checkpoint(
            conn, tenant_id=tenant_id, checkpoint_id=checkpoint_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(checkpoint_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.dim_qc_checkpoints SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_checkpoint(
        conn, tenant_id=tenant_id, checkpoint_id=checkpoint_id,
    )


async def soft_delete_checkpoint(
    conn: Any, *, tenant_id: str, actor_user_id: str, checkpoint_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.dim_qc_checkpoints "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, checkpoint_id, tenant_id,
    )
    return result.endswith(" 1")


# ── Checks (append-only) ───────────────────────────────────────────────


async def list_checks(
    conn: Any,
    *,
    tenant_id: str,
    checkpoint_id: str | None = None,
    batch_id: str | None = None,
    outcome_id: int | None = None,
    kitchen_id: str | None = None,
    raw_material_lot: str | None = None,
    performed_by_user_id: str | None = None,
    ts_after: Any = None,
    ts_before: Any = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1"]
    if checkpoint_id is not None:
        params.append(checkpoint_id)
        clauses.append(f"checkpoint_id = ${len(params)}")
    if batch_id is not None:
        params.append(batch_id)
        clauses.append(f"batch_id = ${len(params)}")
    if outcome_id is not None:
        params.append(outcome_id)
        clauses.append(f"outcome_id = ${len(params)}")
    if kitchen_id is not None:
        params.append(kitchen_id)
        clauses.append(f"kitchen_id = ${len(params)}")
    if raw_material_lot is not None:
        params.append(raw_material_lot)
        clauses.append(f"raw_material_lot = ${len(params)}")
    if performed_by_user_id is not None:
        params.append(performed_by_user_id)
        clauses.append(f"performed_by_user_id = ${len(params)}")
    if ts_after is not None:
        params.append(ts_after)
        clauses.append(f"ts >= ${len(params)}")
    if ts_before is not None:
        params.append(ts_before)
        clauses.append(f"ts <= ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_qc_checks "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY ts DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_check(
    conn: Any, *, tenant_id: str, check_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_qc_checks "
        "WHERE id = $1 AND tenant_id = $2",
        check_id, tenant_id,
    )
    return dict(row) if row else None


async def create_check(
    conn: Any,
    *,
    tenant_id: str,
    performed_by_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.evt_qc_checks "
        "(id, tenant_id, checkpoint_id, batch_id, raw_material_lot, "
        " kitchen_id, outcome_id, measured_value, measured_unit_id, "
        " notes, photo_vault_key, performed_by_user_id, metadata) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)",
        new_id,
        tenant_id,
        data["checkpoint_id"],
        data.get("batch_id"),
        data.get("raw_material_lot"),
        data.get("kitchen_id"),
        int(data["outcome_id"]),
        data.get("measured_value"),
        data.get("measured_unit_id"),
        data.get("notes"),
        data.get("photo_vault_key"),
        performed_by_user_id,
        data.get("metadata") or {},
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_qc_checks WHERE id = $1", new_id,
    )
    return dict(row) if row else {}

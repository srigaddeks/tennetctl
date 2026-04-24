"""Subscriptions repository — raw asyncpg against schema "11_somaerp".

Reads v_subscription_plans / v_subscription_plan_items / v_subscriptions.
Writes fct_subscription_plans (soft-delete), dtl_subscription_plan_items
(soft-delete), fct_subscriptions (soft-delete), evt_subscription_events
(append-only).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Existence checks ────────────────────────────────────────────────────

async def frequency_exists(conn: Any, *, frequency_id: int) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.dim_subscription_frequencies "
        "WHERE id = $1 AND deprecated_at IS NULL",
        frequency_id,
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


async def product_exists(
    conn: Any, *, tenant_id: str, product_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_products "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        product_id, tenant_id,
    )
    return row is not None


async def variant_exists_for_product(
    conn: Any, *, tenant_id: str, variant_id: str, product_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_product_variants "
        "WHERE id = $1 AND tenant_id = $2 AND product_id = $3 "
        "AND deleted_at IS NULL",
        variant_id, tenant_id, product_id,
    )
    return row is not None


async def service_zone_exists(
    conn: Any, *, tenant_id: str, service_zone_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_service_zones "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        service_zone_id, tenant_id,
    )
    return row is not None


# ── Frequencies (read-only) ─────────────────────────────────────────────

async def list_frequencies(conn: Any) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {SCHEMA}.dim_subscription_frequencies "
        "WHERE deprecated_at IS NULL "
        "ORDER BY deliveries_per_week DESC, id ASC"
    )
    return [dict(r) for r in rows]


# ── Plans ───────────────────────────────────────────────────────────────

async def list_plans(
    conn: Any,
    *,
    tenant_id: str,
    status: str | None = None,
    frequency_id: int | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1"]
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if frequency_id is not None:
        params.append(frequency_id)
        clauses.append(f"frequency_id = ${len(params)}")
    if q:
        params.append(f"%{q}%")
        clauses.append(f"name ILIKE ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_subscription_plans "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_plan(
    conn: Any, *, tenant_id: str, plan_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_subscription_plans "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        plan_id, tenant_id,
    )
    return dict(row) if row else None


async def create_plan(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.fct_subscription_plans "
        "(id, tenant_id, name, slug, description, frequency_id, "
        " price_per_delivery, currency_code, status, properties, "
        " created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$11)",
        new_id,
        tenant_id,
        data["name"],
        data["slug"],
        data.get("description"),
        int(data["frequency_id"]),
        data.get("price_per_delivery"),
        data["currency_code"],
        data.get("status") or "active",
        data.get("properties") or {},
        actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_subscription_plans WHERE id = $1", new_id,
    )
    return dict(row) if row else {}


_PLAN_COLS = (
    "name", "slug", "description", "frequency_id",
    "price_per_delivery", "currency_code", "status", "properties",
)


async def update_plan(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    plan_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _PLAN_COLS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_plan(conn, tenant_id=tenant_id, plan_id=plan_id)
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(plan_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.fct_subscription_plans SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
        "AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_plan(conn, tenant_id=tenant_id, plan_id=plan_id)


async def soft_delete_plan(
    conn: Any, *, tenant_id: str, actor_user_id: str, plan_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_subscription_plans "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, plan_id, tenant_id,
    )
    return result.endswith(" 1")


async def count_active_subscriptions_for_plan(
    conn: Any, *, tenant_id: str, plan_id: str,
) -> int:
    row = await conn.fetchrow(
        f"SELECT COUNT(*)::INT AS n FROM {SCHEMA}.fct_subscriptions "
        "WHERE tenant_id = $1 AND plan_id = $2 "
        "AND status = 'active' AND deleted_at IS NULL",
        tenant_id, plan_id,
    )
    return int(row["n"]) if row else 0


# ── Plan items ─────────────────────────────────────────────────────────

async def list_plan_items(
    conn: Any, *, tenant_id: str, plan_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {SCHEMA}.v_subscription_plan_items "
        "WHERE plan_id = $1 AND tenant_id = $2 AND deleted_at IS NULL "
        "ORDER BY position ASC, created_at ASC",
        plan_id, tenant_id,
    )
    return [dict(r) for r in rows]


async def get_plan_item(
    conn: Any, *, tenant_id: str, plan_id: str, item_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_subscription_plan_items "
        "WHERE id = $1 AND plan_id = $2 AND tenant_id = $3 "
        "AND deleted_at IS NULL",
        item_id, plan_id, tenant_id,
    )
    return dict(row) if row else None


async def create_plan_item(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    plan_id: str,
    data: dict,
) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {SCHEMA}.dtl_subscription_plan_items "
        "(id, tenant_id, plan_id, product_id, variant_id, "
        " qty_per_delivery, position, notes, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$9)",
        new_id,
        tenant_id,
        plan_id,
        data["product_id"],
        data.get("variant_id"),
        Decimal(str(data["qty_per_delivery"])),
        int(data.get("position") or 0),
        data.get("notes"),
        actor_user_id,
    )
    return await get_plan_item(
        conn, tenant_id=tenant_id, plan_id=plan_id, item_id=new_id,
    ) or {}


_ITEM_COLS = (
    "product_id", "variant_id", "qty_per_delivery", "position", "notes",
)


async def update_plan_item(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    plan_id: str,
    item_id: str,
    patch: dict,
) -> dict | None:
    sets: list[str] = []
    params: list[Any] = []
    for col in _ITEM_COLS:
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            sets.append(f"{col} = ${len(params)}")
    if not sets:
        return await get_plan_item(
            conn, tenant_id=tenant_id, plan_id=plan_id, item_id=item_id,
        )
    params.append(actor_user_id)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(item_id)
    params.append(plan_id)
    params.append(tenant_id)
    sql = (
        f"UPDATE {SCHEMA}.dtl_subscription_plan_items SET {', '.join(sets)} "
        f"WHERE id = ${len(params) - 2} AND plan_id = ${len(params) - 1} "
        f"AND tenant_id = ${len(params)} AND deleted_at IS NULL"
    )
    result = await conn.execute(sql, *params)
    if not result.endswith(" 1"):
        return None
    return await get_plan_item(
        conn, tenant_id=tenant_id, plan_id=plan_id, item_id=item_id,
    )


async def soft_delete_plan_item(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    plan_id: str,
    item_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.dtl_subscription_plan_items "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND plan_id = $3 AND tenant_id = $4 "
        "AND deleted_at IS NULL",
        actor_user_id, item_id, plan_id, tenant_id,
    )
    return result.endswith(" 1")


# ── Subscriptions ──────────────────────────────────────────────────────

async def list_subscriptions(
    conn: Any,
    *,
    tenant_id: str,
    customer_id: str | None = None,
    plan_id: str | None = None,
    status: str | None = None,
    start_date_from: date | None = None,
    start_date_to: date | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1"]
    if not include_deleted:
        clauses.append("deleted_at IS NULL")
    if customer_id is not None:
        params.append(customer_id)
        clauses.append(f"customer_id = ${len(params)}")
    if plan_id is not None:
        params.append(plan_id)
        clauses.append(f"plan_id = ${len(params)}")
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if start_date_from is not None:
        params.append(start_date_from)
        clauses.append(f"start_date >= ${len(params)}")
    if start_date_to is not None:
        params.append(start_date_to)
        clauses.append(f"start_date <= ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f"SELECT * FROM {SCHEMA}.v_subscriptions "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY start_date DESC, created_at DESC "
        f"LIMIT ${len(params) - 1} OFFSET ${len(params)}"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get_subscription(
    conn: Any, *, tenant_id: str, subscription_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_subscriptions "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        subscription_id, tenant_id,
    )
    return dict(row) if row else None


async def create_subscription(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    data: dict,
) -> tuple[dict, str]:
    """Create fct_subscriptions + evt_subscription_events ('started') atomically.
    Returns (subscription_row, event_id)."""
    new_id = _id.uuid7()
    event_id = _id.uuid7()
    async with conn.transaction():
        await conn.execute(
            f"INSERT INTO {SCHEMA}.fct_subscriptions "
            "(id, tenant_id, customer_id, plan_id, service_zone_id, "
            " start_date, end_date, status, billing_cycle, properties, "
            " created_by, updated_by) "
            "VALUES ($1,$2,$3,$4,$5,$6,$7,'active',$8,$9,$10,$10)",
            new_id,
            tenant_id,
            data["customer_id"],
            data["plan_id"],
            data.get("service_zone_id"),
            data["start_date"],
            data.get("end_date"),
            data.get("billing_cycle"),
            data.get("properties") or {},
            actor_user_id,
        )
        await conn.execute(
            f"INSERT INTO {SCHEMA}.evt_subscription_events "
            "(id, tenant_id, subscription_id, event_type, from_date, "
            " to_date, reason, metadata, ts, performed_by_user_id) "
            "VALUES ($1,$2,$3,'started',$4,$5,NULL,$6,CURRENT_TIMESTAMP,$7)",
            event_id,
            tenant_id,
            new_id,
            data["start_date"],
            data.get("end_date"),
            {"source": "create_subscription"},
            actor_user_id,
        )
    row = await get_subscription(
        conn, tenant_id=tenant_id, subscription_id=new_id,
    )
    return (row or {}, event_id)


# Allowed status transitions -> evt event_type emitted.
_STATUS_TRANSITIONS: dict[tuple[str, str], str] = {
    ("active", "paused"):    "paused",
    ("paused", "active"):    "resumed",
    ("active", "cancelled"): "cancelled",
    ("paused", "cancelled"): "cancelled",
    ("active", "ended"):     "ended",
    ("paused", "ended"):     "ended",
}


_SUBSCRIPTION_COLS = (
    "service_zone_id",
    "end_date",
    "billing_cycle",
    "properties",
)


async def patch_subscription(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    existing: dict,
    patch: dict,
) -> tuple[dict, str | None]:
    """Apply status transition + field patches atomically; on transition
    insert evt_subscription_events row.
    Returns (updated_row, event_type_or_None).
    """
    from importlib import import_module as _im
    _err = _im("apps.somaerp.backend.01_core.errors")

    new_status = patch.get("status")
    old_status = existing["status"]
    event_type: str | None = None

    if new_status is not None and new_status != old_status:
        transition_key = (old_status, new_status)
        if transition_key not in _STATUS_TRANSITIONS:
            raise _err.ValidationError(
                f"Invalid status transition {old_status} -> {new_status}.",
                code="INVALID_STATUS_TRANSITION",
            )
        event_type = _STATUS_TRANSITIONS[transition_key]

    set_parts: list[str] = []
    params: list[Any] = []

    if event_type is not None:
        params.append(new_status)
        set_parts.append(f"status = ${len(params)}")

        if event_type == "paused":
            pf = patch.get("paused_from") or date.today()
            params.append(pf)
            set_parts.append(f"paused_from = ${len(params)}")
            if patch.get("paused_to") is not None:
                params.append(patch["paused_to"])
                set_parts.append(f"paused_to = ${len(params)}")
            else:
                set_parts.append("paused_to = NULL")
        elif event_type == "resumed":
            set_parts.append("paused_from = NULL")
            set_parts.append("paused_to = NULL")
        elif event_type in ("cancelled", "ended"):
            # Set end_date if not provided.
            if patch.get("end_date") is not None:
                params.append(patch["end_date"])
                set_parts.append(f"end_date = ${len(params)}")
            elif existing.get("end_date") is None:
                params.append(date.today())
                set_parts.append(f"end_date = ${len(params)}")

    # Non-status field patches.
    for col in _SUBSCRIPTION_COLS:
        # Skip if already handled via transition above.
        if col == "end_date" and event_type in ("cancelled", "ended"):
            continue
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            set_parts.append(f"{col} = ${len(params)}")

    async with conn.transaction():
        if set_parts:
            params.append(actor_user_id)
            set_parts.append(f"updated_by = ${len(params)}")
            set_parts.append("updated_at = CURRENT_TIMESTAMP")
            params.append(existing["id"])
            params.append(tenant_id)
            sql = (
                f"UPDATE {SCHEMA}.fct_subscriptions SET {', '.join(set_parts)} "
                f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
                "AND deleted_at IS NULL"
            )
            await conn.execute(sql, *params)

        if event_type is not None:
            event_id = _id.uuid7()
            from_date_val: date | None = None
            to_date_val: date | None = None
            if event_type == "paused":
                from_date_val = patch.get("paused_from") or date.today()
                to_date_val = patch.get("paused_to")
            elif event_type == "resumed":
                from_date_val = date.today()
            elif event_type in ("cancelled", "ended"):
                from_date_val = existing.get("start_date")
                to_date_val = patch.get("end_date") or date.today()

            await conn.execute(
                f"INSERT INTO {SCHEMA}.evt_subscription_events "
                "(id, tenant_id, subscription_id, event_type, from_date, "
                " to_date, reason, metadata, ts, performed_by_user_id) "
                "VALUES ($1,$2,$3,$4,$5,$6,$7,$8,CURRENT_TIMESTAMP,$9)",
                event_id,
                tenant_id,
                existing["id"],
                event_type,
                from_date_val,
                to_date_val,
                patch.get("reason"),
                {"previous_status": old_status, "new_status": new_status},
                actor_user_id,
            )

    row = await get_subscription(
        conn, tenant_id=tenant_id, subscription_id=existing["id"],
    )
    return (row or {}, event_type)


async def soft_delete_subscription(
    conn: Any, *, tenant_id: str, actor_user_id: str, subscription_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_subscriptions "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, subscription_id, tenant_id,
    )
    return result.endswith(" 1")


# ── Events (read-only) ────────────────────────────────────────────────

async def list_subscription_events(
    conn: Any, *, tenant_id: str, subscription_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {SCHEMA}.evt_subscription_events "
        "WHERE subscription_id = $1 AND tenant_id = $2 "
        "ORDER BY ts DESC, created_at DESC",
        subscription_id, tenant_id,
    )
    return [dict(r) for r in rows]

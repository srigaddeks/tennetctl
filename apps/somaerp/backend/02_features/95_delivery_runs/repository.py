"""Delivery runs + stops repository — raw asyncpg.

Reads v_delivery_runs + v_delivery_stops. Writes fct_delivery_runs
(mutable status per documented deviation) + dtl_delivery_stops (soft-delete).
"""

from __future__ import annotations

from datetime import date, datetime
from importlib import import_module
from typing import Any

_id = import_module("apps.somaerp.backend.01_core.id")

SCHEMA = '"11_somaerp"'


# ── Existence + fetch helpers ────────────────────────────────────────────


async def route_exists_active(
    conn: Any, *, tenant_id: str, route_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_delivery_routes "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        route_id, tenant_id,
    )
    return row is not None


async def rider_exists_active(
    conn: Any, *, tenant_id: str, rider_id: str,
) -> bool:
    row = await conn.fetchrow(
        f"SELECT 1 FROM {SCHEMA}.fct_riders "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        rider_id, tenant_id,
    )
    return row is not None


async def get_route_raw(
    conn: Any, *, tenant_id: str, route_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id, tenant_id, kitchen_id, name, target_window_start, "
        f"       target_window_end, status "
        f"FROM {SCHEMA}.fct_delivery_routes "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        route_id, tenant_id,
    )
    return dict(row) if row else None


# ── Runs CRUD ────────────────────────────────────────────────────────


async def list_runs(
    conn: Any,
    *,
    tenant_id: str,
    route_id: str | None = None,
    rider_id: str | None = None,
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
    if route_id is not None:
        params.append(route_id)
        clauses.append(f"route_id = ${len(params)}")
    if rider_id is not None:
        params.append(rider_id)
        clauses.append(f"rider_id = ${len(params)}")
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
        f"SELECT * FROM {SCHEMA}.v_delivery_runs "
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
        f"SELECT * FROM {SCHEMA}.v_delivery_runs "
        "WHERE id = $1 AND tenant_id = $2 AND deleted_at IS NULL",
        run_id, tenant_id,
    )
    return dict(row) if row else None


async def get_active_run_for_date(
    conn: Any, *, tenant_id: str, route_id: str, run_date_val: date,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id, status FROM {SCHEMA}.fct_delivery_runs "
        "WHERE tenant_id = $1 AND route_id = $2 AND run_date = $3 "
        "AND deleted_at IS NULL AND status <> 'cancelled'",
        tenant_id, route_id, run_date_val,
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
        f"INSERT INTO {SCHEMA}.fct_delivery_runs "
        "(id, tenant_id, route_id, rider_id, run_date, status, "
        " total_stops, completed_stops, missed_stops, notes, properties, "
        " created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,'planned',0,0,0,$6,$7,$8,$8)",
        new_id,
        tenant_id,
        data["route_id"],
        data["rider_id"],
        data["run_date"],
        data.get("notes"),
        data.get("properties") or {},
        actor_user_id,
    )
    return await get_run(conn, tenant_id=tenant_id, run_id=new_id) or {}


_ALLOWED_RUN_TRANSITIONS: dict[str, set[str]] = {
    "planned":    {"in_transit", "cancelled"},
    "in_transit": {"completed", "cancelled"},
    "completed":  set(),
    "cancelled":  set(),
}


async def patch_run(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    existing: dict,
    patch: dict,
) -> tuple[dict, str]:
    """Apply state machine transition + optional field patches.
    Returns (updated_row, event_kind) where event_kind is one of:
    'updated' | 'started' | 'completed' | 'cancelled'.
    """
    from importlib import import_module as _im
    _err = _im("apps.somaerp.backend.01_core.errors")

    new_status = patch.get("status")
    old_status = existing["status"]
    event_kind = "updated"

    set_parts: list[str] = []
    params: list[Any] = []

    if new_status is not None and new_status != old_status:
        allowed = _ALLOWED_RUN_TRANSITIONS.get(old_status, set())
        if new_status not in allowed:
            raise _err.ValidationError(
                f"Invalid run status transition {old_status} -> {new_status}.",
                code="INVALID_STATUS_TRANSITION",
            )
        if new_status == "in_transit":
            event_kind = "started"
            params.append(new_status)
            set_parts.append(f"status = ${len(params)}")
            params.append(datetime.utcnow())
            set_parts.append(f"started_at = COALESCE(started_at, ${len(params)})")
        elif new_status == "completed":
            # Require all stops resolved unless allow_incomplete_completion.
            if not patch.get("allow_incomplete_completion"):
                unresolved = await conn.fetchval(
                    f"SELECT COUNT(*)::INT FROM {SCHEMA}.dtl_delivery_stops "
                    "WHERE delivery_run_id = $1 AND tenant_id = $2 "
                    "AND status = 'pending' AND deleted_at IS NULL",
                    existing["id"], tenant_id,
                )
                if int(unresolved or 0) > 0:
                    raise _err.ValidationError(
                        f"Cannot complete run with {unresolved} unresolved "
                        "stops. Resolve them or pass allow_incomplete_completion.",
                        code="UNRESOLVED_STOPS",
                    )
            event_kind = "completed"
            params.append(new_status)
            set_parts.append(f"status = ${len(params)}")
            params.append(datetime.utcnow())
            set_parts.append(f"completed_at = ${len(params)}")
        elif new_status == "cancelled":
            event_kind = "cancelled"
            params.append(new_status)
            set_parts.append(f"status = ${len(params)}")

    # Non-status field patches.
    for col in ("rider_id", "notes", "properties"):
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            set_parts.append(f"{col} = ${len(params)}")

    if set_parts:
        params.append(actor_user_id)
        set_parts.append(f"updated_by = ${len(params)}")
        set_parts.append("updated_at = CURRENT_TIMESTAMP")
        params.append(existing["id"])
        params.append(tenant_id)
        sql = (
            f"UPDATE {SCHEMA}.fct_delivery_runs SET {', '.join(set_parts)} "
            f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
            "AND deleted_at IS NULL"
        )
        await conn.execute(sql, *params)

    row = await get_run(conn, tenant_id=tenant_id, run_id=existing["id"])
    return (row or {}, event_kind)


async def soft_delete_run(
    conn: Any, *, tenant_id: str, actor_user_id: str, run_id: str,
) -> bool:
    result = await conn.execute(
        f"UPDATE {SCHEMA}.fct_delivery_runs "
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, run_id, tenant_id,
    )
    return result.endswith(" 1")


# ── Stops ──────────────────────────────────────────────────────────────


async def list_stops(
    conn: Any, *, tenant_id: str, run_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {SCHEMA}.v_delivery_stops "
        "WHERE delivery_run_id = $1 AND tenant_id = $2 "
        "AND deleted_at IS NULL "
        "ORDER BY sequence_position ASC",
        run_id, tenant_id,
    )
    return [dict(r) for r in rows]


async def get_stop(
    conn: Any, *, tenant_id: str, run_id: str, stop_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {SCHEMA}.v_delivery_stops "
        "WHERE id = $1 AND delivery_run_id = $2 AND tenant_id = $3 "
        "AND deleted_at IS NULL",
        stop_id, run_id, tenant_id,
    )
    return dict(row) if row else None


async def generate_stops(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    run_row: dict,
    route_row: dict,
) -> int:
    """Atomic: read lnk_route_customers for route in sequence order, insert
    one dtl_delivery_stops per customer with status='pending',
    scheduled_at = run_date + route.target_window_start, update run.total_stops.
    Returns number of stops generated."""
    run_id = run_row["id"]
    run_date_val: date = run_row["run_date"]
    window_start = route_row.get("target_window_start")
    if window_start is not None:
        scheduled_at = datetime.combine(run_date_val, window_start)
    else:
        scheduled_at = datetime.combine(run_date_val, datetime.min.time())

    async with conn.transaction():
        lrc_rows = await conn.fetch(
            f"SELECT customer_id, sequence_position "
            f"FROM {SCHEMA}.lnk_route_customers "
            "WHERE route_id = $1 AND tenant_id = $2 "
            "ORDER BY sequence_position ASC",
            route_row["id"], tenant_id,
        )
        count = 0
        for lr in lrc_rows:
            stop_id = _id.uuid7()
            await conn.execute(
                f"INSERT INTO {SCHEMA}.dtl_delivery_stops "
                "(id, tenant_id, delivery_run_id, customer_id, "
                " sequence_position, scheduled_at, status, properties, "
                " created_by, updated_by) "
                "VALUES ($1,$2,$3,$4,$5,$6,'pending','{}'::jsonb,$7,$7)",
                stop_id,
                tenant_id,
                run_id,
                lr["customer_id"],
                int(lr["sequence_position"]),
                scheduled_at,
                actor_user_id,
            )
            count += 1

        await conn.execute(
            f"UPDATE {SCHEMA}.fct_delivery_runs "
            "SET total_stops = $1, "
            "    completed_stops = 0, "
            "    missed_stops = 0, "
            "    updated_at = CURRENT_TIMESTAMP, "
            "    updated_by = $2 "
            "WHERE id = $3 AND tenant_id = $4",
            count, actor_user_id, run_id, tenant_id,
        )
    return count


_COMPLETED_STATUSES = {"delivered"}
_MISSED_STATUSES = {"missed", "customer_unavailable"}


async def patch_stop(
    conn: Any,
    *,
    tenant_id: str,
    actor_user_id: str,
    run_id: str,
    existing_stop: dict,
    patch: dict,
) -> tuple[dict, str | None]:
    """Update stop status + fields; atomically adjust run counters based on
    status transition. Returns (stop_row, event_kind_or_None).
    event_kind in {delivered, missed, rescheduled, cancelled} when status
    transitions.
    """
    from importlib import import_module as _im
    _err = _im("apps.somaerp.backend.01_core.errors")

    new_status = patch.get("status")
    old_status = existing_stop["status"]
    event_kind: str | None = None

    valid_new = {
        "delivered", "missed", "customer_unavailable", "cancelled", "rescheduled",
    }

    set_parts: list[str] = []
    params: list[Any] = []

    if new_status is not None and new_status != old_status:
        if old_status != "pending":
            # Allow re-marking within resolved states? Plan spec focuses on
            # pending->X. Permit for operator correction but audit it.
            pass
        if new_status not in valid_new:
            raise _err.ValidationError(
                f"Invalid stop status {new_status}.",
                code="INVALID_STOP_STATUS",
            )
        params.append(new_status)
        set_parts.append(f"status = ${len(params)}")
        if new_status == "delivered":
            event_kind = "delivered"
            actual = patch.get("actual_at") or datetime.utcnow()
            params.append(actual)
            set_parts.append(f"actual_at = ${len(params)}")
        elif new_status in ("missed", "customer_unavailable"):
            event_kind = "missed"
        elif new_status == "rescheduled":
            event_kind = "rescheduled"
        elif new_status == "cancelled":
            event_kind = "cancelled"

    for col in ("notes", "photo_vault_key", "signature_vault_key"):
        if col in patch and patch[col] is not None:
            params.append(patch[col])
            set_parts.append(f"{col} = ${len(params)}")
    # actual_at patch (without status change) allowed explicitly.
    if (
        "actual_at" in patch
        and patch["actual_at"] is not None
        and new_status != "delivered"
    ):
        params.append(patch["actual_at"])
        set_parts.append(f"actual_at = ${len(params)}")

    async with conn.transaction():
        if set_parts:
            params.append(actor_user_id)
            set_parts.append(f"updated_by = ${len(params)}")
            set_parts.append("updated_at = CURRENT_TIMESTAMP")
            params.append(existing_stop["id"])
            params.append(tenant_id)
            sql = (
                f"UPDATE {SCHEMA}.dtl_delivery_stops SET {', '.join(set_parts)} "
                f"WHERE id = ${len(params) - 1} AND tenant_id = ${len(params)} "
                "AND deleted_at IS NULL"
            )
            await conn.execute(sql, *params)

        # Adjust counters only when status actually changed.
        if new_status is not None and new_status != old_status:
            was_completed = old_status in _COMPLETED_STATUSES
            was_missed = old_status in _MISSED_STATUSES
            is_completed = new_status in _COMPLETED_STATUSES
            is_missed = new_status in _MISSED_STATUSES

            comp_delta = (1 if is_completed else 0) - (1 if was_completed else 0)
            miss_delta = (1 if is_missed else 0) - (1 if was_missed else 0)

            if comp_delta != 0 or miss_delta != 0:
                await conn.execute(
                    f"UPDATE {SCHEMA}.fct_delivery_runs "
                    "SET completed_stops = GREATEST(0, completed_stops + $1), "
                    "    missed_stops    = GREATEST(0, missed_stops + $2), "
                    "    updated_at = CURRENT_TIMESTAMP, "
                    "    updated_by = $3 "
                    "WHERE id = $4 AND tenant_id = $5",
                    comp_delta, miss_delta, actor_user_id, run_id, tenant_id,
                )

    row = await get_stop(
        conn, tenant_id=tenant_id, run_id=run_id, stop_id=existing_stop["id"],
    )
    return (row or {}, event_kind)


# ── Board ─────────────────────────────────────────────────────────────


async def get_board(
    conn: Any, *, tenant_id: str, on_date: date,
) -> dict:
    rows = await conn.fetch(
        f"SELECT * FROM {SCHEMA}.v_delivery_runs "
        "WHERE tenant_id = $1 AND run_date = $2 AND deleted_at IS NULL "
        "ORDER BY kitchen_name ASC, route_name ASC, created_at ASC",
        tenant_id, on_date,
    )
    kitchens: dict[str, dict] = {}
    for r in rows:
        rd = dict(r)
        kid = rd.get("kitchen_id") or "_unknown_"
        if kid not in kitchens:
            kitchens[kid] = {
                "kitchen_id": kid,
                "kitchen_name": rd.get("kitchen_name"),
                "runs": [],
            }
        kitchens[kid]["runs"].append(rd)
    return {
        "date": on_date,
        "kitchens": list(kitchens.values()),
    }

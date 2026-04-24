"""Reporting repository — raw asyncpg queries over v_* views.

All reads. No writes. No mutations. No seeds.
"""

from __future__ import annotations

from datetime import date
from typing import Any


SCHEMA = '"11_somaerp"'


# ── Dashboard ────────────────────────────────────────────────────────────


async def select_dashboard_today(
    conn: Any,
    *,
    tenant_id: str,
    as_of_date: date | None = None,
) -> dict:
    """Return KPI snapshot for `as_of_date` (defaults to today).

    When as_of_date is today we can use v_dashboard_today directly; otherwise
    we recompute the same shape against the raw tables with a parameterized
    date. Either way the output shape is identical.
    """
    if as_of_date is None:
        row = await conn.fetchrow(
            f"SELECT tenant_id, date, active_batches, completed_batches, "
            f"in_transit_runs, completed_runs, scheduled_deliveries, "
            f"completed_deliveries, active_subscriptions "
            f"FROM {SCHEMA}.v_dashboard_today "
            "WHERE tenant_id = $1",
            tenant_id,
        )
        if row is not None:
            return dict(row)
        # Fallback if tenant has no kitchens yet — return zeros with today.
        row2 = await conn.fetchrow("SELECT CURRENT_DATE AS today")
        return {
            "tenant_id": tenant_id,
            "date": row2["today"],
            "active_batches": 0,
            "completed_batches": 0,
            "in_transit_runs": 0,
            "completed_runs": 0,
            "scheduled_deliveries": 0,
            "completed_deliveries": 0,
            "active_subscriptions": 0,
        }

    # Historical/future date — parameterized recomputation.
    sql = f"""
    SELECT
        $1::VARCHAR AS tenant_id,
        $2::DATE AS date,
        COALESCE((
            SELECT COUNT(*)::INT FROM {SCHEMA}.fct_production_batches b
            WHERE b.tenant_id = $1 AND b.run_date = $2
              AND b.status IN ('planned','in_progress')
              AND b.deleted_at IS NULL
        ), 0) AS active_batches,
        COALESCE((
            SELECT COUNT(*)::INT FROM {SCHEMA}.fct_production_batches b
            WHERE b.tenant_id = $1 AND b.run_date = $2
              AND b.status = 'completed' AND b.deleted_at IS NULL
        ), 0) AS completed_batches,
        COALESCE((
            SELECT COUNT(*)::INT FROM {SCHEMA}.fct_delivery_runs r
            WHERE r.tenant_id = $1 AND r.run_date = $2
              AND r.status = 'in_transit' AND r.deleted_at IS NULL
        ), 0) AS in_transit_runs,
        COALESCE((
            SELECT COUNT(*)::INT FROM {SCHEMA}.fct_delivery_runs r
            WHERE r.tenant_id = $1 AND r.run_date = $2
              AND r.status = 'completed' AND r.deleted_at IS NULL
        ), 0) AS completed_runs,
        COALESCE((
            SELECT COUNT(*)::INT FROM {SCHEMA}.dtl_delivery_stops s
            JOIN {SCHEMA}.fct_delivery_runs r
              ON r.id = s.delivery_run_id AND r.tenant_id = s.tenant_id
            WHERE s.tenant_id = $1 AND r.run_date = $2
              AND s.deleted_at IS NULL AND r.deleted_at IS NULL
        ), 0) AS scheduled_deliveries,
        COALESCE((
            SELECT COUNT(*)::INT FROM {SCHEMA}.dtl_delivery_stops s
            JOIN {SCHEMA}.fct_delivery_runs r
              ON r.id = s.delivery_run_id AND r.tenant_id = s.tenant_id
            WHERE s.tenant_id = $1 AND r.run_date = $2
              AND s.status = 'delivered'
              AND s.deleted_at IS NULL AND r.deleted_at IS NULL
        ), 0) AS completed_deliveries,
        COALESCE((
            SELECT COUNT(*)::INT FROM {SCHEMA}.fct_subscriptions s
            WHERE s.tenant_id = $1 AND s.status = 'active'
              AND s.deleted_at IS NULL
        ), 0) AS active_subscriptions
    """
    row = await conn.fetchrow(sql, tenant_id, as_of_date)
    return dict(row) if row else {}


# ── Yield / COGS trends ──────────────────────────────────────────────────


def _bucket_date_expr(bucket: str) -> str:
    if bucket == "weekly":
        return "DATE_TRUNC('week', run_date)::date"
    if bucket == "monthly":
        return "DATE_TRUNC('month', run_date)::date"
    return "run_date"


async def list_yield_trends(
    conn: Any,
    *,
    tenant_id: str,
    from_date: date,
    to_date: date,
    kitchen_id: str | None = None,
    product_id: str | None = None,
    bucket: str = "daily",
) -> list[dict]:
    date_expr = _bucket_date_expr(bucket)
    params: list[Any] = [tenant_id, from_date, to_date]
    clauses = [
        "tenant_id = $1",
        "run_date >= $2",
        "run_date <= $3",
    ]
    if kitchen_id is not None:
        params.append(kitchen_id)
        clauses.append(f"kitchen_id = ${len(params)}")
    if product_id is not None:
        params.append(product_id)
        clauses.append(f"product_id = ${len(params)}")
    sql = (
        f"SELECT {date_expr} AS date, kitchen_id, "
        f"MIN(kitchen_name) AS kitchen_name, "
        f"product_id, MIN(product_name) AS product_name, "
        f"SUM(planned_qty) AS planned_qty, "
        f"SUM(actual_qty) AS actual_qty, "
        f"AVG(yield_pct) AS yield_pct, "
        f"SUM(batch_count)::INT AS batch_count "
        f"FROM {SCHEMA}.v_batch_yield_daily "
        f"WHERE {' AND '.join(clauses)} "
        f"GROUP BY {date_expr}, kitchen_id, product_id "
        f"ORDER BY {date_expr} ASC, kitchen_id, product_id"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def list_cogs_trends(
    conn: Any,
    *,
    tenant_id: str,
    from_date: date,
    to_date: date,
    kitchen_id: str | None = None,
    product_id: str | None = None,
    bucket: str = "daily",
) -> list[dict]:
    date_expr = _bucket_date_expr(bucket)
    params: list[Any] = [tenant_id, from_date, to_date]
    clauses = [
        "tenant_id = $1",
        "run_date >= $2",
        "run_date <= $3",
    ]
    if kitchen_id is not None:
        params.append(kitchen_id)
        clauses.append(f"kitchen_id = ${len(params)}")
    if product_id is not None:
        params.append(product_id)
        clauses.append(f"product_id = ${len(params)}")
    sql = (
        f"SELECT {date_expr} AS date, kitchen_id, "
        f"MIN(kitchen_name) AS kitchen_name, "
        f"product_id, MIN(product_name) AS product_name, "
        f"SUM(total_cogs) AS total_cogs, "
        f"AVG(cogs_per_unit) AS cogs_per_unit, "
        f"SUM(batch_count)::INT AS batch_count, "
        f"MAX(currency_code) AS currency_code "
        f"FROM {SCHEMA}.v_batch_cogs_daily "
        f"WHERE {' AND '.join(clauses)} "
        f"GROUP BY {date_expr}, kitchen_id, product_id "
        f"ORDER BY {date_expr} ASC, kitchen_id, product_id"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


# ── Inventory alerts ─────────────────────────────────────────────────────


async def list_inventory_alerts(
    conn: Any,
    *,
    tenant_id: str,
    kitchen_id: str | None = None,
    severity: str | None = None,  # 'critical' | 'low' | 'all' (default all)
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1"]
    if kitchen_id is not None:
        params.append(kitchen_id)
        clauses.append(f"kitchen_id = ${len(params)}")
    if severity == "critical":
        clauses.append("alert_level = 'critical'")
    elif severity == "low":
        clauses.append("alert_level IN ('critical','low')")
    sql = (
        f"SELECT kitchen_id, kitchen_name, raw_material_id, raw_material_name, "
        f"category_name, current_qty, unit_code, reorder_point_qty, "
        f"alert_level, primary_supplier_id, primary_supplier_name "
        f"FROM {SCHEMA}.v_inventory_reorder_alerts "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY CASE alert_level "
        f"  WHEN 'critical' THEN 0 "
        f"  WHEN 'low' THEN 1 "
        f"  ELSE 2 END, "
        f"kitchen_name, raw_material_name"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


# ── Procurement spend ────────────────────────────────────────────────────


async def list_procurement_spend(
    conn: Any,
    *,
    tenant_id: str,
    from_date: date,
    to_date: date,
    kitchen_id: str | None = None,
    supplier_id: str | None = None,
) -> list[dict]:
    params: list[Any] = [
        tenant_id,
        from_date.strftime("%Y-%m"),
        to_date.strftime("%Y-%m"),
    ]
    clauses = [
        "tenant_id = $1",
        "year_month >= $2",
        "year_month <= $3",
    ]
    if kitchen_id is not None:
        params.append(kitchen_id)
        clauses.append(f"kitchen_id = ${len(params)}")
    if supplier_id is not None:
        params.append(supplier_id)
        clauses.append(f"supplier_id = ${len(params)}")
    sql = (
        f"SELECT year_month, kitchen_id, kitchen_name, supplier_id, "
        f"supplier_name, total_spend, currency_code, run_count, line_count "
        f"FROM {SCHEMA}.v_procurement_spend_monthly "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY year_month ASC, kitchen_name, supplier_name"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


# ── Revenue projection ───────────────────────────────────────────────────


async def list_revenue_projection(
    conn: Any,
    *,
    tenant_id: str,
    status: str | None = "active",
    as_of_date: date | None = None,
) -> list[dict]:
    params: list[Any] = [tenant_id]
    clauses = ["tenant_id = $1"]
    if status is not None:
        params.append(status)
        clauses.append(f"status = ${len(params)}")
    if as_of_date is not None:
        params.append(as_of_date)
        clauses.append(
            f"start_date <= ${len(params)} "
            f"AND (end_date IS NULL OR end_date >= ${len(params)})"
        )
    sql = (
        f"SELECT subscription_id, customer_name, plan_name, frequency_code, "
        f"price_per_delivery, deliveries_per_week, weekly_projected, "
        f"daily_projected, monthly_projected, currency_code "
        f"FROM {SCHEMA}.v_subscription_revenue_projected "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY monthly_projected DESC NULLS LAST, customer_name"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


# ── Compliance ───────────────────────────────────────────────────────────


async def list_compliance_batches(
    conn: Any,
    *,
    tenant_id: str,
    from_date: date,
    to_date: date,
    product_id: str | None = None,
) -> list[dict]:
    params: list[Any] = [tenant_id, from_date, to_date]
    clauses = [
        "b.tenant_id = $1",
        "b.run_date >= $2",
        "b.run_date <= $3",
    ]
    if product_id is not None:
        params.append(product_id)
        clauses.append(f"EXISTS ("
                       f"SELECT 1 FROM {SCHEMA}.fct_production_batches pb "
                       f"WHERE pb.id = b.batch_id AND pb.product_id = ${len(params)})")
    sql = (
        f"SELECT b.batch_id, b.run_date, b.product_name, b.recipe_version, "
        f"b.kitchen_name, b.planned_qty, b.actual_qty, b.lot_numbers, "
        f"b.qc_results, b.completed_by "
        f"FROM {SCHEMA}.v_fssai_compliance_batches b "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY b.run_date DESC, b.product_name"
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]

"""Reports repository — direct SQL analytics against schema "12_somacrm"."""

from __future__ import annotations

from typing import Any

SCHEMA = '"12_somacrm"'


async def pipeline_summary(conn: Any, *, tenant_id: str) -> dict:
    rows = await conn.fetch(
        f"""
        SELECT
            d.stage_id,
            ps.name AS stage_name,
            ps.color AS stage_color,
            ps.order_position AS stage_order,
            COUNT(d.id) AS deal_count,
            SUM(d.value) AS total_value
        FROM {SCHEMA}."fct_deals" d
        LEFT JOIN {SCHEMA}."fct_pipeline_stages" ps ON ps.id = d.stage_id
        WHERE d.tenant_id = $1 AND d.deleted_at IS NULL
        GROUP BY d.stage_id, ps.name, ps.color, ps.order_position
        ORDER BY ps.order_position ASC NULLS LAST
        """,
        tenant_id,
    )
    stages = [dict(r) for r in rows]
    totals = await conn.fetchrow(
        f"SELECT COUNT(*) AS total_deals, SUM(value) AS total_value "
        f"FROM {SCHEMA}.\"fct_deals\" WHERE tenant_id = $1 AND deleted_at IS NULL",
        tenant_id,
    )
    return {
        "stages": stages,
        "total_deals": totals["total_deals"] or 0,
        "total_value": totals["total_value"],
    }


async def lead_conversion(conn: Any, *, tenant_id: str) -> dict:
    rows = await conn.fetch(
        f"""
        SELECT
            s.code AS status,
            COUNT(l.id) AS lead_count
        FROM {SCHEMA}."fct_leads" l
        JOIN {SCHEMA}."dim_lead_statuses" s ON s.id = l.status_id
        WHERE l.tenant_id = $1 AND l.deleted_at IS NULL
        GROUP BY s.code, s.id
        ORDER BY s.id ASC
        """,
        tenant_id,
    )
    by_status = [dict(r) for r in rows]
    total = sum(r["lead_count"] for r in by_status)
    return {"by_status": by_status, "total_leads": total}


async def activity_summary(conn: Any, *, tenant_id: str) -> dict:
    rows = await conn.fetch(
        f"""
        SELECT
            at2.code AS activity_type,
            ast.code AS status,
            COUNT(a.id) AS count
        FROM {SCHEMA}."fct_activities" a
        JOIN {SCHEMA}."dim_activity_types" at2 ON at2.id = a.activity_type_id
        JOIN {SCHEMA}."dim_activity_statuses" ast ON ast.id = a.status_id
        WHERE a.tenant_id = $1 AND a.deleted_at IS NULL
        GROUP BY at2.code, at2.id, ast.code, ast.id
        ORDER BY at2.id ASC, ast.id ASC
        """,
        tenant_id,
    )
    data = [dict(r) for r in rows]
    total = sum(r["count"] for r in data)
    return {"rows": data, "total": total}


async def contact_growth(conn: Any, *, tenant_id: str, weeks: int = 12) -> dict:
    rows = await conn.fetch(
        f"""
        SELECT
            TO_CHAR(DATE_TRUNC('week', created_at), 'IYYY-IW') AS week,
            COUNT(*) AS new_contacts
        FROM {SCHEMA}."fct_contacts"
        WHERE tenant_id = $1
          AND deleted_at IS NULL
          AND created_at >= CURRENT_TIMESTAMP - ($2 * INTERVAL '1 week')
        GROUP BY DATE_TRUNC('week', created_at)
        ORDER BY DATE_TRUNC('week', created_at) ASC
        """,
        tenant_id, weeks,
    )
    return {"weeks": [dict(r) for r in rows]}

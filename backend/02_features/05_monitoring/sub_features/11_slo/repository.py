"""Repository layer for monitoring.slos — reads views, writes facts + details."""

from __future__ import annotations

from typing import Any

from importlib import import_module

_core_id: Any = import_module("backend.01_core.id")


# ── SLO CRUD ──────────────────────────────────────────────────────────────


async def create_slo(
    conn: Any,
    *,
    id: str,
    org_id: str,
    workspace_id: str | None,
    name: str,
    slug: str,
    description: str | None,
    indicator_kind_id: int,
    window_kind_id: int,
    target_pct: float,
    severity_id: int,
    owner_user_id: str | None,
    created_by: str,
) -> dict[str, Any]:
    """Insert SLO into fct_monitoring_slos. Returns the inserted row."""
    row = await conn.fetchrow(
        """
        INSERT INTO "05_monitoring"."10_fct_monitoring_slos"
            (id, org_id, workspace_id, name, slug, description,
             indicator_kind_id, window_kind_id, target_pct, severity_id,
             owner_user_id, is_active, created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, true, $12, $12, NOW(), NOW())
        RETURNING *
        """,
        id, org_id, workspace_id, name, slug, description,
        indicator_kind_id, window_kind_id, target_pct, severity_id,
        owner_user_id, created_by,
    )
    return dict(row) if row else {}


async def create_slo_indicator(
    conn: Any,
    *,
    slo_id: str,
    good_query: str | None,
    total_query: str | None,
    threshold_metric_id: str | None,
    threshold_value: float | None,
    threshold_op: str | None,
    latency_percentile: float | None,
) -> None:
    """Insert SLO indicator into dtl_monitoring_slo_indicator."""
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."20_dtl_monitoring_slo_indicator"
            (slo_id, good_query, total_query, threshold_metric_id,
             threshold_value, threshold_op, latency_percentile, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """,
        slo_id, good_query, total_query, threshold_metric_id,
        threshold_value, threshold_op, latency_percentile,
    )


async def create_slo_burn_thresholds(
    conn: Any,
    *,
    slo_id: str,
    fast_window_seconds: int,
    fast_burn_rate: float,
    slow_window_seconds: int,
    slow_burn_rate: float,
    page_on_fast: bool,
    page_on_slow: bool,
) -> None:
    """Insert SLO burn thresholds into dtl_monitoring_slo_burn_thresholds."""
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."21_dtl_monitoring_slo_burn_thresholds"
            (slo_id, fast_window_seconds, fast_burn_rate,
             slow_window_seconds, slow_burn_rate, page_on_fast, page_on_slow,
             created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """,
        slo_id, fast_window_seconds, fast_burn_rate,
        slow_window_seconds, slow_burn_rate, page_on_fast, page_on_slow,
    )


async def update_slo(
    conn: Any,
    *,
    slo_id: str,
    name: str | None = None,
    description: str | None = None,
    target_pct: float | None = None,
    is_active: bool | None = None,
    owner_user_id: str | None = None,
    severity_id: int | None = None,
    updated_by: str,
) -> dict[str, Any]:
    """Partial update of SLO. Returns updated row."""
    updates = []
    params = [slo_id, updated_by]

    if name is not None:
        updates.append("name = $3")
        params.append(name)
    if description is not None:
        updates.append(f"description = ${len(params) + 1}")
        params.append(description)
    if target_pct is not None:
        updates.append(f"target_pct = ${len(params) + 1}")
        params.append(target_pct)
    if is_active is not None:
        updates.append(f"is_active = ${len(params) + 1}")
        params.append(is_active)
    if owner_user_id is not None:
        updates.append(f"owner_user_id = ${len(params) + 1}")
        params.append(owner_user_id)
    if severity_id is not None:
        updates.append(f"severity_id = ${len(params) + 1}")
        params.append(severity_id)

    if not updates:
        # No changes; return current row
        return await get_slo_by_id(conn, slo_id)

    updates.append("updated_by = $2")
    updates.append("updated_at = NOW()")

    sql = f"""
        UPDATE "05_monitoring"."10_fct_monitoring_slos"
        SET {', '.join(updates)}
        WHERE id = $1
        RETURNING *
    """

    row = await conn.fetchrow(sql, *params)
    return dict(row) if row else {}


async def soft_delete_slo(conn: Any, slo_id: str, updated_by: str) -> None:
    """Soft-delete an SLO by setting deleted_at."""
    await conn.execute(
        """
        UPDATE "05_monitoring"."10_fct_monitoring_slos"
        SET deleted_at = NOW(), updated_by = $2, updated_at = NOW()
        WHERE id = $1
        """,
        slo_id, updated_by,
    )


async def get_slo_by_id(conn: Any, slo_id: str) -> dict[str, Any]:
    """Fetch a single SLO by ID from v_monitoring_slos."""
    row = await conn.fetchrow(
        'SELECT * FROM "05_monitoring".v_monitoring_slos WHERE id = $1',
        slo_id,
    )
    return dict(row) if row else {}


async def list_slos(
    conn: Any,
    *,
    org_id: str,
    status: str | None = None,
    window_kind: str | None = None,
    owner_user_id: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """List SLOs with optional filters. Returns (rows, total_count)."""
    where_clauses = ['org_id = $1']
    params: list[Any] = [org_id]

    if status:
        where_clauses.append(f'status = ${len(params) + 1}')
        params.append(status)
    if window_kind:
        where_clauses.append(f'window_kind_code = ${len(params) + 1}')
        params.append(window_kind)
    if owner_user_id:
        where_clauses.append(f'owner_user_id = ${len(params) + 1}')
        params.append(owner_user_id)
    if q:
        where_clauses.append(f'(name ILIKE ${len(params) + 1} OR slug ILIKE ${len(params) + 1})')
        params.extend([f'%{q}%', f'%{q}%'])

    where_sql = ' AND '.join(where_clauses)

    # Total count
    count_sql = f'SELECT COUNT(*) as cnt FROM "05_monitoring".v_monitoring_slos WHERE {where_sql}'
    count_row = await conn.fetchrow(count_sql, *params)
    total = count_row["cnt"] if count_row else 0

    # Paginated list
    list_sql = f"""
        SELECT * FROM "05_monitoring".v_monitoring_slos
        WHERE {where_sql}
        ORDER BY created_at DESC
        LIMIT ${ len(params) + 1} OFFSET ${len(params) + 2}
    """
    params.extend([limit, offset])

    rows = await conn.fetch(list_sql, *params)
    return [dict(r) for r in rows], total


async def severity_id_by_code(conn: Any, code: str) -> int | None:
    """Look up severity dim table by code."""
    row = await conn.fetchrow(
        'SELECT id FROM "05_monitoring"."01_dim_monitoring_alert_severity" WHERE code = $1',
        code,
    )
    return row["id"] if row else None


async def indicator_kind_id_by_code(conn: Any, code: str) -> int | None:
    """Look up indicator kind dim table by code."""
    row = await conn.fetchrow(
        'SELECT id FROM "05_monitoring"."01_dim_monitoring_slo_indicator_kind" WHERE code = $1',
        code,
    )
    return row["id"] if row else None


async def window_kind_id_by_code(conn: Any, code: str) -> int | None:
    """Look up window kind dim table by code."""
    row = await conn.fetchrow(
        'SELECT id FROM "05_monitoring"."02_dim_monitoring_slo_window_kind" WHERE code = $1',
        code,
    )
    return row["id"] if row else None


# ── Evaluation persistence ────────────────────────────────────────────────


async def insert_evaluation(
    conn: Any,
    *,
    id: str,
    slo_id: str,
    org_id: str,
    window_start: Any,  # datetime
    window_end: Any,
    good_count: int,
    total_count: int,
    attainment_pct: float,
    budget_remaining_pct: float,
    burn_rate_1h: float,
    burn_rate_6h: float,
    burn_rate_24h: float,
    burn_rate_3d: float,
) -> None:
    """Insert evaluation row into evt_monitoring_slo_evaluations."""
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."60_evt_monitoring_slo_evaluations"
            (id, slo_id, org_id, window_start, window_end,
             good_count, total_count, attainment_pct, budget_remaining_pct,
             burn_rate_1h, burn_rate_6h, burn_rate_24h, burn_rate_3d, evaluated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW())
        """,
        id, slo_id, org_id, window_start, window_end,
        good_count, total_count, attainment_pct, budget_remaining_pct,
        burn_rate_1h, burn_rate_6h, burn_rate_24h, burn_rate_3d,
    )


async def get_latest_evaluation(conn: Any, slo_id: str) -> dict[str, Any] | None:
    """Fetch the most recent evaluation for an SLO."""
    row = await conn.fetchrow(
        """
        SELECT * FROM "05_monitoring"."60_evt_monitoring_slo_evaluations"
        WHERE slo_id = $1
        ORDER BY evaluated_at DESC
        LIMIT 1
        """,
        slo_id,
    )
    return dict(row) if row else None


async def list_evaluations(
    conn: Any,
    *,
    slo_id: str,
    from_ts: Any,  # datetime
    to_ts: Any,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """List evaluation rows for an SLO in a time range."""
    rows = await conn.fetch(
        """
        SELECT * FROM "05_monitoring"."60_evt_monitoring_slo_evaluations"
        WHERE slo_id = $1 AND evaluated_at >= $2 AND evaluated_at < $3
        ORDER BY evaluated_at DESC
        LIMIT $4
        """,
        slo_id, from_ts, to_ts, limit,
    )
    return [dict(r) for r in rows]


# ── Breach tracking ───────────────────────────────────────────────────────


async def insert_breach(
    conn: Any,
    *,
    id: str,
    slo_id: str,
    org_id: str,
    breach_kind: str,
    burn_rate: float | None = None,
    alert_event_id: str | None = None,
) -> None:
    """Insert a breach event."""
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."61_evt_monitoring_slo_breaches"
            (id, slo_id, org_id, breach_kind, burn_rate, alert_event_id, occurred_at)
        VALUES ($1, $2, $3, $4, $5, $6, NOW())
        """,
        id, slo_id, org_id, breach_kind, burn_rate, alert_event_id,
    )


async def get_open_breach(
    conn: Any,
    slo_id: str,
    breach_kind: str,
) -> dict[str, Any] | None:
    """Check if an unresolved breach of a given kind exists."""
    row = await conn.fetchrow(
        """
        SELECT * FROM "05_monitoring"."61_evt_monitoring_slo_breaches"
        WHERE slo_id = $1 AND breach_kind = $2 AND resolved_at IS NULL
        """,
        slo_id, breach_kind,
    )
    return dict(row) if row else None


async def resolve_breach(conn: Any, breach_id: str) -> None:
    """Mark a breach as resolved."""
    await conn.execute(
        'UPDATE "05_monitoring"."61_evt_monitoring_slo_breaches" '
        'SET resolved_at = NOW() WHERE id = $1',
        breach_id,
    )


__all__ = [
    "create_slo",
    "create_slo_indicator",
    "create_slo_burn_thresholds",
    "update_slo",
    "soft_delete_slo",
    "get_slo_by_id",
    "list_slos",
    "severity_id_by_code",
    "indicator_kind_id_by_code",
    "window_kind_id_by_code",
    "insert_evaluation",
    "get_latest_evaluation",
    "list_evaluations",
    "insert_breach",
    "get_open_breach",
    "resolve_breach",
]

"""
product_ops.events — repository (asyncpg raw SQL only).

Reads target views (v_visitors, v_product_events). Writes target raw
fct_/lnk_/evt_ tables. No business logic — that's the service's job.

Project conventions:
- conn (not pool) is passed in. Pool acquisition belongs in routes.
- asyncpg handles dicts↔JSONB transparently — never call json.dumps().
- IDs are VARCHAR(36) UUID v7 (uuid7() from backend.01_core.id).
- Time columns are TIMESTAMP (tz-naive UTC); callers strip tzinfo.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ── Visitors ────────────────────────────────────────────────────────

async def upsert_visitor(
    conn: Any,
    *,
    visitor_id: str,
    anonymous_id: str,
    workspace_id: str,
    org_id: str,
    occurred_at: datetime,
    first_touch: dict[str, Any] | None,
) -> str:
    """
    Insert a visitor row if anonymous_id is new; otherwise update last_seen
    (and last-touch if first_touch != None and represents a new touch).

    Returns the canonical visitor_id (existing row's id if present, else new).

    First-touch is sticky: only set on INSERT, never overwritten on UPDATE.
    Last-touch always updates. last_* columns aren't materialized on
    fct_visitors (Phase 48 may add them; for now they live in evt_attribution_touches
    and get resolved via product_ops.events.attribution_resolve).
    """
    ft = first_touch or {}
    row = await conn.fetchrow(
        """
        INSERT INTO "10_product_ops"."10_fct_visitors"
            (id, anonymous_id, org_id, workspace_id,
             first_seen, last_seen,
             first_utm_source_id, first_utm_medium, first_utm_campaign,
             first_utm_term, first_utm_content,
             first_referrer, first_landing_url,
             created_at, updated_at)
        VALUES ($1, $2, $3, $4,
                $5, $5,
                $6, $7, $8,
                $9, $10,
                $11, $12,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (anonymous_id) DO UPDATE
            SET last_seen = GREATEST("10_fct_visitors".last_seen, EXCLUDED.last_seen),
                updated_at = CURRENT_TIMESTAMP
        RETURNING id
        """,
        visitor_id, anonymous_id, org_id, workspace_id,
        occurred_at,
        ft.get("utm_source_id"), ft.get("utm_medium"), ft.get("utm_campaign"),
        ft.get("utm_term"), ft.get("utm_content"),
        ft.get("referrer"), ft.get("landing_url"),
    )
    return row["id"]


async def set_visitor_user_id(conn: Any, *, visitor_id: str, user_id: str) -> None:
    """Resolve an anonymous visitor to an IAM user. Idempotent."""
    await conn.execute(
        """
        UPDATE "10_product_ops"."10_fct_visitors"
           SET user_id = $1, updated_at = CURRENT_TIMESTAMP
         WHERE id = $2
        """,
        user_id, visitor_id,
    )


async def add_visitor_alias(conn: Any, *, visitor_id: str, alias_anonymous_id: str, org_id: str) -> bool:
    """
    Add an alias row pointing alias_anonymous_id at visitor_id. Idempotent
    via UNIQUE constraint on alias_anonymous_id. Returns True if inserted.
    """
    from importlib import import_module
    _id: Any = import_module("backend.01_core.id")
    try:
        await conn.execute(
            """
            INSERT INTO "10_product_ops"."40_lnk_visitor_aliases"
                (id, visitor_id, alias_anonymous_id, org_id)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (alias_anonymous_id) DO NOTHING
            """,
            _id.uuid7(), visitor_id, alias_anonymous_id, org_id,
        )
        return True
    except Exception:
        return False


async def get_visitor_by_id(conn: Any, visitor_id: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT id, anonymous_id, user_id, org_id, workspace_id,
               first_seen, last_seen,
               first_utm_source, first_utm_medium, first_utm_campaign,
               first_utm_term, first_utm_content,
               first_referrer, first_landing_url,
               is_active, is_deleted, created_at, updated_at
          FROM "10_product_ops".v_visitors
         WHERE id = $1
        """,
        visitor_id,
    )
    return dict(row) if row else None


# ── Attribution sources (intern-on-write dim) ────────────────────────

async def intern_attribution_source(conn: Any, code: str) -> int:
    """
    INSERT … ON CONFLICT (code) DO UPDATE … RETURNING id pattern.

    The DO UPDATE on `code = code` is a no-op that still triggers RETURNING
    on conflict (without it, RETURNING is empty on conflict-skip).
    """
    row = await conn.fetchrow(
        """
        INSERT INTO "10_product_ops"."02_dim_attribution_sources" (code)
        VALUES ($1)
        ON CONFLICT (code) DO UPDATE SET code = EXCLUDED.code
        RETURNING id
        """,
        code.lower().strip()[:256],
    )
    return int(row["id"])


# ── Events ──────────────────────────────────────────────────────────

async def bulk_insert_events(conn: Any, rows: list[dict]) -> int:
    """
    Bulk insert into evt_product_events. Uses executemany since asyncpg
    handles parameterization safely. Returns number of rows written.

    `metadata` (JSONB) is passed as a Python dict; asyncpg's JSONB codec
    (registered on pool init in 01_core.database) converts transparently.
    """
    if not rows:
        return 0
    await conn.executemany(
        """
        INSERT INTO "10_product_ops"."60_evt_product_events"
            (id, visitor_id, user_id, session_id, org_id, workspace_id,
             event_kind_id, event_name, occurred_at, page_url, referrer,
             metadata, created_at)
        VALUES ($1, $2, $3, $4, $5, $6,
                $7, $8, $9, $10, $11,
                $12, CURRENT_TIMESTAMP)
        """,
        [
            (
                r["id"], r["visitor_id"], r.get("user_id"), r.get("session_id"),
                r["org_id"], r["workspace_id"],
                r["event_kind_id"], r.get("event_name"),
                r["occurred_at"], r.get("page_url"), r.get("referrer"),
                r.get("metadata") or {},
            )
            for r in rows
        ],
    )
    return len(rows)


async def bulk_insert_touches(conn: Any, rows: list[dict]) -> int:
    """Same shape as events; daily-partitioned table."""
    if not rows:
        return 0
    await conn.executemany(
        """
        INSERT INTO "10_product_ops"."60_evt_attribution_touches"
            (id, visitor_id, org_id, workspace_id, occurred_at,
             utm_source_id, utm_medium, utm_campaign, utm_term, utm_content,
             referrer, landing_url, metadata, created_at)
        VALUES ($1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10,
                $11, $12, $13, CURRENT_TIMESTAMP)
        """,
        [
            (
                r["id"], r["visitor_id"], r["org_id"], r["workspace_id"], r["occurred_at"],
                r.get("utm_source_id"), r.get("utm_medium"), r.get("utm_campaign"),
                r.get("utm_term"), r.get("utm_content"),
                r.get("referrer"), r.get("landing_url"),
                r.get("metadata") or {},
            )
            for r in rows
        ],
    )
    return len(rows)


async def count_distinct_event_names_today(conn: Any, workspace_id: str) -> int:
    """
    Cardinality cap query — count distinct event_name in this workspace
    for today's partition. Reads partition directly (no parent-table scan)
    via WHERE on occurred_at to enable partition pruning.
    """
    row = await conn.fetchrow(
        """
        SELECT COUNT(DISTINCT event_name)::int AS n
          FROM "10_product_ops"."60_evt_product_events"
         WHERE workspace_id = $1
           AND event_name IS NOT NULL
           AND occurred_at >= CURRENT_DATE
           AND occurred_at <  CURRENT_DATE + INTERVAL '1 day'
        """,
        workspace_id,
    )
    return int(row["n"]) if row else 0


# ── Read path ───────────────────────────────────────────────────────

async def list_events(
    conn: Any,
    *,
    workspace_id: str,
    limit: int = 100,
    cursor: str | None = None,
) -> list[dict]:
    """
    Cursor-paginated reverse-chronological list. Cursor is the ISO-formatted
    occurred_at of the last row returned (simple time cursor; ties broken by id).
    """
    if cursor:
        rows = await conn.fetch(
            """
            SELECT id, visitor_id, user_id, session_id, org_id, workspace_id,
                   event_kind, event_name, occurred_at, page_url, referrer,
                   metadata, created_at
              FROM "10_product_ops".v_product_events
             WHERE workspace_id = $1
               AND occurred_at < $2::timestamp
             ORDER BY occurred_at DESC, id DESC
             LIMIT $3
            """,
            workspace_id, cursor, limit,
        )
    else:
        rows = await conn.fetch(
            """
            SELECT id, visitor_id, user_id, session_id, org_id, workspace_id,
                   event_kind, event_name, occurred_at, page_url, referrer,
                   metadata, created_at
              FROM "10_product_ops".v_product_events
             WHERE workspace_id = $1
             ORDER BY occurred_at DESC, id DESC
             LIMIT $2
            """,
            workspace_id, limit,
        )
    return [dict(r) for r in rows]


async def funnel_query(
    conn: Any,
    *,
    workspace_id: str,
    steps: list[str],
    days: int = 30,
) -> list[dict]:
    """
    Sequential funnel: count distinct visitors who completed step N within
    the time window after completing step N-1. steps is a list of event_name
    values; the funnel measures conversion from step[0] to each subsequent step.

    Implementation: for each step, find visitors whose earliest step-N event
    occurred AFTER their earliest step-(N-1) event. SQL CTE-per-step.

    Returns list of {step, event_name, visitors, conversion_rate_from_first}.
    """
    if not steps:
        return []

    # Build the CTE chain. Param numbering: $1=workspace_id, $2..$(N+1)=event_names,
    # $(N+2)=days. event_name values are parameterized (safe); the `s{i}` CTE
    # identifiers are positionally generated, not user-controlled.
    counts_select = ", ".join(
        [f"(SELECT COUNT(*)::int FROM s{i}) AS step_{i}_visitors"
         for i in range(len(steps))]
    )

    ctes2: list[str] = []
    for i, _ in enumerate(steps):
        name_param = f"${i+2}"
        days_param = f"${len(steps)+2}"
        if i == 0:
            ctes2.append(
                f"""s0 AS (
                    SELECT visitor_id, MIN(occurred_at) AS first_at
                      FROM "10_product_ops"."60_evt_product_events"
                     WHERE workspace_id = $1
                       AND event_name = {name_param}
                       AND occurred_at >= CURRENT_DATE - ({days_param}::int * INTERVAL '1 day')
                     GROUP BY visitor_id
                )"""
            )
        else:
            ctes2.append(
                f"""s{i} AS (
                    SELECT e.visitor_id, MIN(e.occurred_at) AS first_at
                      FROM "10_product_ops"."60_evt_product_events" e
                      JOIN s{i-1} p ON p.visitor_id = e.visitor_id
                     WHERE e.workspace_id = $1
                       AND e.event_name = {name_param}
                       AND e.occurred_at > p.first_at
                       AND e.occurred_at >= CURRENT_DATE - ({days_param}::int * INTERVAL '1 day')
                     GROUP BY e.visitor_id
                )"""
            )
    sql = f"WITH {', '.join(ctes2)} SELECT {counts_select}"

    args: list[Any] = [workspace_id] + list(steps) + [days]
    row = await conn.fetchrow(sql, *args)
    if not row:
        return []

    base = int(row["step_0_visitors"]) or 0
    out: list[dict] = []
    for i, name in enumerate(steps):
        v = int(row[f"step_{i}_visitors"])
        rate = (v / base * 100) if base > 0 else 0.0
        out.append({
            "step": i,
            "event_name": name,
            "visitors": v,
            "conversion_rate_from_first": round(rate, 2),
        })
    return out


async def retention_matrix(
    conn: Any,
    *,
    workspace_id: str,
    cohort_event: str,
    return_event: str,
    weeks: int = 8,
) -> list[dict]:
    """
    Weekly retention. For each cohort-week W, count visitors whose first
    cohort_event landed in W; then for each subsequent week W+k, count how
    many of those same visitors had a return_event.

    Returns list of {cohort_week, cohort_size, retained_w0..w_{weeks-1}}.
    """
    rows = await conn.fetch(
        """
        WITH cohort AS (
            SELECT visitor_id,
                   date_trunc('week', MIN(occurred_at))::date AS cohort_week
              FROM "10_product_ops"."60_evt_product_events"
             WHERE workspace_id = $1
               AND event_name = $2
               AND occurred_at >= CURRENT_DATE - ($4::int * 7 * INTERVAL '1 day')
             GROUP BY visitor_id
        ),
        returns AS (
            SELECT e.visitor_id,
                   date_trunc('week', e.occurred_at)::date AS event_week
              FROM "10_product_ops"."60_evt_product_events" e
              JOIN cohort c ON c.visitor_id = e.visitor_id
             WHERE e.workspace_id = $1
               AND e.event_name = $3
               AND e.occurred_at >= c.cohort_week
        )
        SELECT c.cohort_week,
               COUNT(DISTINCT c.visitor_id)::int AS cohort_size,
               COALESCE(json_agg(DISTINCT (r.event_week - c.cohort_week) / 7) FILTER (WHERE r.visitor_id IS NOT NULL), '[]'::json) AS retained_weeks
          FROM cohort c
          LEFT JOIN returns r ON r.visitor_id = c.visitor_id
         GROUP BY c.cohort_week
         ORDER BY c.cohort_week DESC
         LIMIT $4
        """,
        workspace_id, cohort_event, return_event, weeks,
    )
    return [dict(r) for r in rows]


async def utm_campaign_aggregate(
    conn: Any,
    *,
    workspace_id: str,
    days: int = 30,
) -> list[dict]:
    """
    UTM dashboard aggregate. For each (utm_source, utm_campaign) seen in
    evt_attribution_touches over the last N days, count distinct visitors
    and (best-effort) conversions where conversion = any event with
    metadata->>'is_conversion' = 'true'.

    Reads partitioned tables; date-window WHERE enables partition pruning.
    """
    rows = await conn.fetch(
        """
        WITH touched AS (
            SELECT t.visitor_id,
                   COALESCE(s.code, '(direct)') AS utm_source,
                   COALESCE(t.utm_campaign, '(none)') AS utm_campaign
              FROM "10_product_ops"."60_evt_attribution_touches" t
              LEFT JOIN "10_product_ops"."02_dim_attribution_sources" s
                     ON s.id = t.utm_source_id
             WHERE t.workspace_id = $1
               AND t.occurred_at >= CURRENT_DATE - ($2::int * INTERVAL '1 day')
        ),
        conversions AS (
            SELECT DISTINCT visitor_id
              FROM "10_product_ops"."60_evt_product_events"
             WHERE workspace_id = $1
               AND occurred_at >= CURRENT_DATE - ($2::int * INTERVAL '1 day')
               AND (metadata->>'is_conversion') = 'true'
        )
        SELECT t.utm_source,
               t.utm_campaign,
               COUNT(DISTINCT t.visitor_id)::int AS visitors,
               COUNT(DISTINCT c.visitor_id)::int AS conversions
          FROM touched t
          LEFT JOIN conversions c ON c.visitor_id = t.visitor_id
         GROUP BY t.utm_source, t.utm_campaign
         ORDER BY visitors DESC, conversions DESC
         LIMIT 200
        """,
        workspace_id, days,
    )
    return [dict(r) for r in rows]


async def get_last_touch_for_visitor(conn: Any, visitor_id: str) -> dict | None:
    """Most-recent evt_attribution_touches row for this visitor."""
    row = await conn.fetchrow(
        """
        SELECT t.id, t.visitor_id, t.occurred_at,
               s.code AS utm_source,
               t.utm_medium, t.utm_campaign, t.utm_term, t.utm_content,
               t.referrer, t.landing_url
          FROM "10_product_ops"."60_evt_attribution_touches" t
          LEFT JOIN "10_product_ops"."02_dim_attribution_sources" s
                 ON s.id = t.utm_source_id
         WHERE t.visitor_id = $1
         ORDER BY t.occurred_at DESC, t.id DESC
         LIMIT 1
        """,
        visitor_id,
    )
    return dict(row) if row else None

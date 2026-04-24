"""
audit.events — asyncpg repository (read path).

Queries against "04_audit"."v_audit_events". The view LEFT JOINs dim_audit_categories
and dim_audit_event_keys to evt_audit, so unregistered event keys still return
the row with NULL event_label / event_description.

Cursor pagination: cursor is a base64url-encoded JSON {created_at, id} pair
(UUID v7 ids are time-sortable, and (created_at, id) is the natural sort key).

Event-key globbing: translates '*' → '%' in a LIKE pattern.

Metadata substring match: `metadata::text ILIKE '%' || $N || '%'`. Simple ILIKE
for now; upgrade to `@@ to_tsquery` in a future plan if needed.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any


_VIEW = '"04_audit"."v_audit_events"'


def _encode_cursor(created_at: datetime, row_id: str) -> str:
    """Encode (created_at, id) into an opaque base64url string."""
    ts = created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)
    raw = json.dumps({"created_at": ts, "id": row_id}).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    """Decode cursor → (created_at, id). Raises ValueError on malformed input."""
    pad = "=" * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode((cursor + pad).encode("ascii"))
        payload = json.loads(raw)
    except Exception as e:
        raise ValueError(f"invalid cursor: {cursor!r}") from e
    ts_str = payload["created_at"]
    ts = datetime.fromisoformat(ts_str)
    # asyncpg returns naive TIMESTAMP values; strip tz if present for comparison.
    if ts.tzinfo is not None:
        ts = ts.astimezone(timezone.utc).replace(tzinfo=None)
    return ts, str(payload["id"])


def _build_where(filters: dict[str, Any]) -> tuple[str, list[Any]]:
    """
    Build WHERE fragment + positional params list from a filter dict.
    Only non-None filter entries contribute predicates.
    """
    clauses: list[str] = []
    params: list[Any] = []

    def _p(value: Any) -> str:
        params.append(value)
        return f"${len(params)}"

    event_key = filters.get("event_key")
    if event_key is not None:
        if "*" in event_key:
            pattern = event_key.replace("*", "%")
            clauses.append(f"event_key LIKE {_p(pattern)}")
        else:
            clauses.append(f"event_key = {_p(event_key)}")

    for col in (
        "category_code",
        "outcome",
        "actor_user_id",
        "actor_session_id",
        "org_id",
        "workspace_id",
        "application_id",
        "trace_id",
    ):
        v = filters.get(col)
        if v is not None:
            clauses.append(f"{col} = {_p(v)}")

    since = filters.get("since")
    if since is not None:
        clauses.append(f"created_at >= {_p(since)}")
    until = filters.get("until")
    if until is not None:
        clauses.append(f"created_at <= {_p(until)}")

    q = filters.get("q")
    if q is not None and q != "":
        clauses.append(f"metadata::text ILIKE '%' || {_p(q)} || '%'")

    where_sql = " AND ".join(clauses) if clauses else "TRUE"
    return where_sql, params


async def list_events(
    conn: Any,
    *,
    filters: dict[str, Any],
    cursor: str | None,
    limit: int,
) -> tuple[list[dict], str | None]:
    """
    Return (items, next_cursor). items has up to `limit` rows ordered by
    created_at DESC, id DESC. next_cursor is None if there are no more rows.
    """
    where_sql, params = _build_where(filters)

    if cursor is not None:
        cursor_ts, cursor_id = _decode_cursor(cursor)
        params.extend([cursor_ts, cursor_id])
        cursor_ts_idx = len(params) - 1
        cursor_id_idx = len(params)
        cursor_clause = f"(created_at, id) < (${cursor_ts_idx}, ${cursor_id_idx})"
        where_sql = f"({where_sql}) AND {cursor_clause}"

    # Fetch limit + 1 to detect more-rows-available.
    params_page = [*params, limit + 1]
    limit_idx = len(params_page)

    sql = (
        f"SELECT id, event_key, event_label, event_description, "
        f"       category_code, category_label, "
        f"       actor_user_id, actor_session_id, org_id, workspace_id, "
        f"       application_id, "
        f"       trace_id, span_id, parent_span_id, "
        f"       outcome, metadata, created_at "
        f"FROM {_VIEW} "
        f"WHERE {where_sql} "
        f"ORDER BY created_at DESC, id DESC "
        f"LIMIT ${limit_idx}"
    )
    rows = await conn.fetch(sql, *params_page)
    items = [dict(r) for r in rows]

    next_cursor: str | None = None
    if len(items) > limit:
        # Drop the overflow row + encode cursor from the LAST kept row.
        items = items[:limit]
        last = items[-1]
        next_cursor = _encode_cursor(last["created_at"], last["id"])

    return items, next_cursor


async def get_event(conn: Any, event_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id, event_key, event_label, event_description, "
        f"       category_code, category_label, "
        f"       actor_user_id, actor_session_id, org_id, workspace_id, "
        f"       application_id, "
        f"       trace_id, span_id, parent_span_id, "
        f"       outcome, metadata, created_at "
        f"FROM {_VIEW} WHERE id = $1",
        event_id,
    )
    return dict(row) if row else None


async def stats(
    conn: Any,
    *,
    filters: dict[str, Any],
    bucket: str,
) -> dict:
    """
    Compute aggregates: top-50 by event_key, all outcomes, all categories,
    time-series per hour or day.
    """
    where_sql, params = _build_where(filters)

    by_key_rows = await conn.fetch(
        f"SELECT event_key, COUNT(*)::BIGINT AS count "
        f"FROM {_VIEW} WHERE {where_sql} "
        f"GROUP BY event_key ORDER BY count DESC LIMIT 50",
        *params,
    )
    by_outcome_rows = await conn.fetch(
        f"SELECT outcome, COUNT(*)::BIGINT AS count "
        f"FROM {_VIEW} WHERE {where_sql} "
        f"GROUP BY outcome ORDER BY count DESC",
        *params,
    )
    by_category_rows = await conn.fetch(
        f"SELECT category_code, COUNT(*)::BIGINT AS count "
        f"FROM {_VIEW} WHERE {where_sql} "
        f"GROUP BY category_code ORDER BY count DESC",
        *params,
    )

    # date_trunc on hour|day with ISO-8601 text output for the bucket label
    trunc_unit = "hour" if bucket == "hour" else "day"
    time_series_rows = await conn.fetch(
        f"SELECT to_char(date_trunc('{trunc_unit}', created_at), 'YYYY-MM-DD\"T\"HH24:MI:SS') AS bucket, "
        f"       COUNT(*)::BIGINT AS count "
        f"FROM {_VIEW} WHERE {where_sql} "
        f"GROUP BY date_trunc('{trunc_unit}', created_at) "
        f"ORDER BY date_trunc('{trunc_unit}', created_at) ASC",
        *params,
    )

    return {
        "by_event_key":   [{"event_key":     r["event_key"],     "count": int(r["count"])} for r in by_key_rows],
        "by_outcome":     [{"outcome":       r["outcome"],       "count": int(r["count"])} for r in by_outcome_rows],
        "by_category":    [{"category_code": r["category_code"], "count": int(r["count"])} for r in by_category_rows],
        "time_series":    [{"bucket":        r["bucket"],        "count": int(r["count"])} for r in time_series_rows],
    }


async def list_event_keys(conn: Any) -> tuple[list[dict], int]:
    rows = await conn.fetch(
        'SELECT k.key, k.label, k.description, c.code AS category_code, k.deprecated_at '
        'FROM "04_audit"."02_dim_audit_event_keys" k '
        'JOIN "04_audit"."01_dim_audit_categories" c ON c.id = k.category_id '
        'ORDER BY k.key ASC'
    )
    items = [dict(r) for r in rows]
    return items, len(items)


_EVT = '"04_audit"."60_evt_audit"'


async def funnel_analysis(
    conn: Any,
    *,
    steps: list[str],
    org_id: str | None,
    since: datetime | None,
    until: datetime | None,
) -> list[dict]:
    """
    Simplified funnel: each step is a separate fetchval call with explicit params.
    Avoids the complex param-renaming problem.
    """
    results: list[dict] = []
    step0_count: int = 0

    for i, key in enumerate(steps):
        if i == 0:
            count = await _funnel_step0(conn, event_key=key, org_id=org_id, since=since, until=until)
            step0_count = count
            pct = 100.0
        else:
            count = await _funnel_stepi(
                conn,
                current_key=key,
                prev_key=steps[i - 1],
                org_id=org_id,
                since=since,
                until=until,
            )
            pct = (count / step0_count * 100) if step0_count else 0.0

        results.append({
            "event_key": key,
            "users": count,
            "conversion_pct": round(pct, 1),
        })

    return results


async def _funnel_step0(
    conn: Any,
    *,
    event_key: str,
    org_id: str | None,
    since: datetime | None,
    until: datetime | None,
) -> int:
    params: list[Any] = [event_key]
    clauses = [f"event_key = $1"]

    if org_id is not None:
        params.append(org_id)
        clauses.append(f"org_id = ${len(params)}")
    if since is not None:
        params.append(since)
        clauses.append(f"created_at >= ${len(params)}")
    if until is not None:
        params.append(until)
        clauses.append(f"created_at <= ${len(params)}")

    where = " AND ".join(clauses)
    result = await conn.fetchval(
        f"SELECT COUNT(DISTINCT actor_user_id) FROM {_EVT} WHERE {where}",
        *params,
    )
    return int(result or 0)


async def _funnel_stepi(
    conn: Any,
    *,
    current_key: str,
    prev_key: str,
    org_id: str | None,
    since: datetime | None,
    until: datetime | None,
) -> int:
    """Count actors who did current_key AFTER prev_key (any occurrence before)."""
    params: list[Any] = [current_key, prev_key]
    outer: list[str] = ["e.event_key = $1"]
    inner: list[str] = ["prev.event_key = $2", "prev.actor_user_id = e.actor_user_id", "prev.created_at < e.created_at"]

    if org_id is not None:
        params.append(org_id)
        outer.append(f"e.org_id = ${len(params)}")
        params.append(org_id)
        inner.append(f"prev.org_id = ${len(params)}")
    if since is not None:
        params.append(since)
        outer.append(f"e.created_at >= ${len(params)}")
        params.append(since)
        inner.append(f"prev.created_at >= ${len(params)}")
    if until is not None:
        params.append(until)
        outer.append(f"e.created_at <= ${len(params)}")

    outer_where = " AND ".join(outer)
    inner_where = " AND ".join(inner)

    result = await conn.fetchval(
        f"SELECT COUNT(DISTINCT e.actor_user_id) "
        f"FROM {_EVT} e "
        f"WHERE {outer_where} "
        f"AND EXISTS (SELECT 1 FROM {_EVT} prev WHERE {inner_where})",
        *params,
    )
    return int(result or 0)


async def retention_analysis(
    conn: Any,
    *,
    anchor: str,
    return_event: str,
    org_id: str | None,
    bucket: str,
    periods: int,
) -> dict:
    """
    Cohort retention: actors who did `anchor` are grouped by cohort_period
    (date_trunc of bucket). For each cohort, count how many returned with
    `return_event` in each subsequent period offset (0=same period, 1=next, ...).
    """
    trunc = "week" if bucket == "week" else "day"

    params: list[Any] = [anchor, return_event]
    org_clause_anchor = ""
    org_clause_return = ""

    if org_id is not None:
        params.append(org_id)
        org_clause_anchor = f"AND org_id = ${len(params)}"
        params.append(org_id)
        org_clause_return = f"AND e.org_id = ${len(params)}"

    params.append(periods)
    periods_idx = len(params)

    sql = f"""
WITH cohort_members AS (
    SELECT
        actor_user_id,
        date_trunc('{trunc}', created_at) AS cohort_period,
        MIN(created_at) AS first_seen
    FROM {_EVT}
    WHERE event_key = $1 {org_clause_anchor}
    GROUP BY actor_user_id, date_trunc('{trunc}', created_at)
),
cohort_sizes AS (
    SELECT cohort_period, COUNT(DISTINCT actor_user_id) AS cohort_size
    FROM cohort_members GROUP BY cohort_period
),
return_events AS (
    SELECT
        c.actor_user_id,
        c.cohort_period,
        EXTRACT(EPOCH FROM (date_trunc('{trunc}', e.created_at) - c.cohort_period))::BIGINT
            / EXTRACT(EPOCH FROM INTERVAL '1 {trunc}')::BIGINT AS period_offset
    FROM cohort_members c
    JOIN {_EVT} e ON e.actor_user_id = c.actor_user_id
    WHERE e.event_key = $2 {org_clause_return}
    AND date_trunc('{trunc}', e.created_at) >= c.cohort_period
)
SELECT
    to_char(cs.cohort_period, 'YYYY-MM-DD') AS cohort_period,
    cs.cohort_size,
    r.period_offset,
    COUNT(DISTINCT r.actor_user_id) AS returned_count
FROM cohort_sizes cs
LEFT JOIN return_events r ON r.cohort_period = cs.cohort_period
    AND r.period_offset BETWEEN 0 AND ${periods_idx}
GROUP BY cs.cohort_period, cs.cohort_size, r.period_offset
ORDER BY cs.cohort_period, r.period_offset
"""

    rows = await conn.fetch(sql, *params)

    # Post-process into nested structure.
    cohort_map: dict[str, dict] = {}
    for row in rows:
        cp = row["cohort_period"]
        if cp not in cohort_map:
            cohort_map[cp] = {
                "cohort_period": cp,
                "cohort_size": int(row["cohort_size"]),
                "retained_map": {},
            }
        offset = row["period_offset"]
        if offset is not None:
            cohort_map[cp]["retained_map"][int(offset)] = int(row["returned_count"])

    cohorts = []
    for cp, c in sorted(cohort_map.items()):
        size = c["cohort_size"]
        retained = []
        for off in range(periods + 1):
            count = c["retained_map"].get(off, 0)
            pct = round(count / size * 100, 1) if size else 0.0
            retained.append({"offset": off, "count": count, "pct": pct})
        cohorts.append({
            "cohort_period": cp,
            "cohort_size": size,
            "retained": retained,
        })

    return {"cohorts": cohorts}


async def upsert_event_key(
    conn: Any,
    *,
    key: str,
    label: str,
    description: str | None,
    category_code: str,
) -> None:
    """
    Idempotent upsert for auto-sync of observed event keys. Resolves category_code
    → category_id via dim_audit_categories lookup. Reused by boot-time sync and
    tests.
    """
    cat_id = await conn.fetchval(
        'SELECT id FROM "04_audit"."01_dim_audit_categories" WHERE code = $1',
        category_code,
    )
    if cat_id is None:
        raise ValueError(f"unknown audit category: {category_code!r}")

    await conn.execute(
        'INSERT INTO "04_audit"."02_dim_audit_event_keys" '
        '    (key, label, description, category_id) '
        'VALUES ($1, $2, $3, $4) '
        'ON CONFLICT (key) DO UPDATE SET '
        '    label = EXCLUDED.label, '
        '    description = EXCLUDED.description, '
        '    category_id = EXCLUDED.category_id',
        key, label, description, cat_id,
    )

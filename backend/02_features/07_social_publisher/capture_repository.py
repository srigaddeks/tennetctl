"""social_publisher.capture — repository layer (raw asyncpg SQL)."""
from __future__ import annotations

import datetime as dt
import logging
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")

logger = logging.getLogger("tennetctl.social.capture")

_TABLE   = '"07_social"."62_evt_social_captures"'
_VIEW    = '"07_social"."v_social_captures"'
_METRICS = '"07_social"."63_evt_capture_metrics"'

_PLATFORM_IDS: dict[str, int] = {}
_TYPE_IDS: dict[str, int] = {}


async def _ensure_dims(conn: Any) -> None:
    global _PLATFORM_IDS, _TYPE_IDS
    if not _PLATFORM_IDS:
        rows = await conn.fetch('SELECT id, code FROM "07_social"."01_dim_platforms"')
        _PLATFORM_IDS = {r["code"]: r["id"] for r in rows}
    if not _TYPE_IDS:
        rows = await conn.fetch('SELECT id, code FROM "07_social"."03_dim_capture_types"')
        _TYPE_IDS = {r["code"]: r["id"] for r in rows}


async def bulk_insert(
    conn: Any,
    *,
    user_id: str,
    org_id: str,
    workspace_id: str | None,
    captures: list[dict],
) -> tuple[list[str], int, int]:
    """
    Insert captures with dedup. On duplicate, append a row to the metric-
    observations table so engagement time-series is preserved.

    Returns (inserted_ids, deduped_count, metric_observations_recorded).
    """
    await _ensure_dims(conn)

    inserted_ids: list[str] = []
    deduped = 0
    metric_observations = 0

    for c in captures:
        platform_code = c["platform"]
        platform_id = _PLATFORM_IDS.get(platform_code)
        type_id = _TYPE_IDS.get(c["type"])
        if platform_id is None or type_id is None:
            logger.warning("Unknown platform=%s or type=%s — skipping", platform_code, c["type"])
            deduped += 1
            continue

        observed = c["observed_at"]
        if isinstance(observed, str):
            observed = dt.datetime.fromisoformat(observed.replace("Z", "+00:00"))
        if observed.tzinfo is not None:
            observed = observed.replace(tzinfo=None)

        row_id = c["id"]
        inserted_pk = await conn.fetchval(
            f"""
            INSERT INTO {_TABLE}
              (id, user_id, org_id, workspace_id, platform_id, type_id, platform_post_id,
               observed_at, extractor_version,
               author_handle, author_name, text_excerpt, url,
               like_count, reply_count, repost_count, view_count,
               is_own, raw_attrs)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19)
            ON CONFLICT (user_id, platform_id, type_id, platform_post_id)
            DO NOTHING
            RETURNING id
            """,
            row_id, user_id, org_id, workspace_id, platform_id, type_id,
            c["platform_post_id"], observed, c.get("extractor_version", "v1"),
            c.get("author_handle"), c.get("author_name"),
            c.get("text_excerpt"), c.get("url"),
            c.get("like_count"), c.get("reply_count"),
            c.get("repost_count"), c.get("view_count"),
            c.get("is_own", False),
            c.get("raw_attrs") or {},
        )

        if inserted_pk is not None:
            inserted_ids.append(row_id)
            continue

        # Duplicate: record a metric observation (engagement time-series).
        # Only insert if at least one metric is non-null, to avoid empty noise.
        has_metric = any(c.get(k) is not None for k in ("like_count", "reply_count", "repost_count", "view_count"))
        if not has_metric:
            deduped += 1
            continue

        existing_capture_id = await conn.fetchval(
            f"""
            SELECT id FROM {_TABLE}
            WHERE user_id = $1 AND platform_id = $2 AND type_id = $3 AND platform_post_id = $4
            """,
            user_id, platform_id, type_id, c["platform_post_id"],
        )
        if existing_capture_id is None:
            deduped += 1
            continue

        reactions = (c.get("raw_attrs") or {}).get("reactions")
        await conn.execute(
            f"""
            INSERT INTO {_METRICS}
              (id, capture_id, user_id, org_id, observed_at,
               like_count, reply_count, repost_count, view_count, reactions)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            """,
            _core_id.uuid7(), existing_capture_id, user_id, org_id, observed,
            c.get("like_count"), c.get("reply_count"),
            c.get("repost_count"), c.get("view_count"),
            reactions,
        )
        metric_observations += 1
        deduped += 1

    return inserted_ids, deduped, metric_observations


async def list_captures(
    conn: Any,
    *,
    user_id: str,
    org_id: str | None = None,
    workspace_id: str | None = None,
    platform: str | None = None,
    capture_type: str | None = None,
    author_handle: str | None = None,
    hashtag: str | None = None,
    mention: str | None = None,
    q: str | None = None,
    from_dt: dt.datetime | None = None,
    to_dt: dt.datetime | None = None,
    is_own: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Return (items, total) filtered by the supplied criteria."""
    await _ensure_dims(conn)

    wheres = ["user_id = $1"]
    params: list[Any] = [user_id]
    idx = 2

    def add(cond: str, value: Any) -> None:
        nonlocal idx
        wheres.append(cond.replace("$$", f"${idx}"))
        params.append(value)
        idx += 1

    if org_id:           add("org_id = $$", org_id)
    if workspace_id:     add("workspace_id = $$", workspace_id)
    if platform:         add("platform = $$", platform)
    if capture_type:     add("type = $$", capture_type)
    if author_handle:    add("author_handle = $$", author_handle)
    if is_own is not None: add("is_own = $$", is_own)
    if from_dt:
        ts = from_dt.replace(tzinfo=None) if from_dt.tzinfo else from_dt
        add("observed_at >= $$", ts)
    if to_dt:
        ts = to_dt.replace(tzinfo=None) if to_dt.tzinfo else to_dt
        add("observed_at <= $$", ts)
    if hashtag:
        # hashtag filter is on raw_attrs.hashtags array — GIN-indexed
        wheres.append(f"raw_attrs -> 'hashtags' ? ${idx}")
        params.append(hashtag); idx += 1
    if mention:
        wheres.append(f"raw_attrs -> 'mentions' ? ${idx}")
        params.append(mention); idx += 1
    if q:
        # Reads the generated column on the underlying fct table via the view
        # (tsvector isn't in the view, so query the table directly).
        # Delegate to table for tsvector; keep rest of the filters working by
        # emitting a separate sub-select.
        wheres.append(
            f"id IN (SELECT id FROM {_TABLE} "
            f"WHERE text_tsv @@ plainto_tsquery('simple', ${idx}))"
        )
        params.append(q); idx += 1

    where_sql = " AND ".join(wheres)
    base = f"FROM {_VIEW} WHERE {where_sql}"

    total = await conn.fetchval(f"SELECT COUNT(*) {base}", *params)
    rows = await conn.fetch(
        f"SELECT * {base} ORDER BY observed_at DESC LIMIT {limit} OFFSET {offset}",
        *params,
    )
    return [dict(r) for r in rows], int(total or 0)


# ── Metric history for a single capture ─────────────────────────────────────

async def metric_history(
    conn: Any,
    *,
    user_id: str,
    capture_id: str,
    limit: int = 200,
) -> list[dict]:
    """Return all metric observations for a capture (ordered oldest→newest)."""
    rows = await conn.fetch(
        f"""
        SELECT observed_at, like_count, reply_count, repost_count, view_count, reactions
        FROM {_METRICS}
        WHERE capture_id = $1 AND user_id = $2
        ORDER BY observed_at ASC
        LIMIT {limit}
        """,
        capture_id, user_id,
    )
    return [dict(r) for r in rows]


# ── Top-N aggregates (insights) ─────────────────────────────────────────────

async def top_authors(
    conn: Any, *, user_id: str, platform: str | None, limit: int,
) -> list[dict]:
    if platform:
        rows = await conn.fetch(
            """
            SELECT handle, display_name, platform, capture_count,
                   total_likes_seen, total_replies_seen, first_seen_at, last_seen_at
            FROM "07_social"."v_social_authors"
            WHERE user_id = $1 AND platform = $2
            ORDER BY capture_count DESC, total_likes_seen DESC NULLS LAST
            LIMIT $3
            """,
            user_id, platform, limit,
        )
    else:
        rows = await conn.fetch(
            """
            SELECT handle, display_name, platform, capture_count,
                   total_likes_seen, total_replies_seen, first_seen_at, last_seen_at
            FROM "07_social"."v_social_authors"
            WHERE user_id = $1
            ORDER BY capture_count DESC, total_likes_seen DESC NULLS LAST
            LIMIT $2
            """,
            user_id, limit,
        )
    return [dict(r) for r in rows]


async def top_hashtags(
    conn: Any, *, user_id: str, platform: str | None, limit: int,
) -> list[dict]:
    platform_clause = "AND platform = $2" if platform else ""
    params: list[Any] = [user_id]
    if platform:
        params.append(platform)
    params.append(limit)
    rows = await conn.fetch(
        f"""
        SELECT tag, COUNT(*)::int AS n
        FROM {_VIEW},
        LATERAL jsonb_array_elements_text(COALESCE(raw_attrs -> 'hashtags', '[]'::jsonb)) AS tag
        WHERE user_id = $1 {platform_clause}
        GROUP BY tag
        ORDER BY n DESC
        LIMIT ${len(params)}
        """,
        *params,
    )
    return [dict(r) for r in rows]


async def capture_counts(conn: Any, *, user_id: str) -> dict:
    """Return aggregate counts for the user's feed (for the Intelligence header)."""
    totals = await conn.fetchrow(
        f"""
        SELECT
          COUNT(*)                                         AS total,
          COUNT(*) FILTER (WHERE is_own)                   AS own_count,
          COUNT(*) FILTER (WHERE observed_at >= (CURRENT_TIMESTAMP - INTERVAL '24 hours')) AS today_count,
          COUNT(*) FILTER (WHERE observed_at >= (CURRENT_TIMESTAMP - INTERVAL '7 days'))   AS week_count
        FROM {_VIEW}
        WHERE user_id = $1
        """,
        user_id,
    )
    by_platform = await conn.fetch(
        f"SELECT platform, COUNT(*)::int AS n FROM {_VIEW} WHERE user_id = $1 GROUP BY platform ORDER BY n DESC",
        user_id,
    )
    by_type = await conn.fetch(
        f"SELECT type, COUNT(*)::int AS n FROM {_VIEW} WHERE user_id = $1 GROUP BY type ORDER BY n DESC",
        user_id,
    )
    return {
        "total":      int(totals["total"] or 0),
        "own_count":  int(totals["own_count"] or 0),
        "today_count":int(totals["today_count"] or 0),
        "week_count": int(totals["week_count"] or 0),
        "by_platform": [dict(r) for r in by_platform],
        "by_type":     [dict(r) for r in by_type],
    }


# ── Retention prune ─────────────────────────────────────────────────────────

async def prune_expired(conn: Any, *, default_days: int = 365) -> int:
    """
    Delete captures past their retention window. Uses per-type
    default_retention_days with the supplied default as fallback.
    Returns number of rows deleted.
    """
    n = await conn.fetchval(
        f"""
        WITH to_delete AS (
          SELECT c.id
          FROM {_TABLE} c
          JOIN "07_social"."03_dim_capture_types" t ON t.id = c.type_id
          WHERE c.observed_at <
                (CURRENT_TIMESTAMP - (COALESCE(t.default_retention_days, $1) || ' days')::interval)
        )
        DELETE FROM {_TABLE} WHERE id IN (SELECT id FROM to_delete)
        RETURNING 1
        """,
        default_days,
    )
    return int(n) if isinstance(n, int) else 0

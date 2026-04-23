"""social_publisher.capture — repository layer (raw asyncpg SQL)."""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

logger = logging.getLogger("tennetctl.social.capture")

_TABLE = '"07_social"."62_evt_social_captures"'
_VIEW  = '"07_social"."v_social_captures"'

# Cached dim lookups (platform + type → smallint id)
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


def _row_to_dict(row: Any) -> dict:
    return dict(row)


async def bulk_insert(
    conn: Any,
    *,
    user_id: str,
    org_id: str,
    captures: list[dict],
) -> tuple[list[str], int]:
    """Insert captures with dedup. Returns (inserted_ids, deduped_count)."""
    await _ensure_dims(conn)

    inserted_ids: list[str] = []
    deduped = 0

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
        # Store as UTC naive
        if observed.tzinfo is not None:
            observed = observed.replace(tzinfo=None)

        row_id = c["id"]
        result = await conn.fetchval(
            f"""
            INSERT INTO {_TABLE}
              (id, user_id, org_id, platform_id, type_id, platform_post_id,
               observed_at, extractor_version,
               author_handle, author_name, text_excerpt, url,
               like_count, reply_count, repost_count, view_count,
               is_own, raw_attrs)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18)
            ON CONFLICT (user_id, platform_id, type_id, platform_post_id)
            DO NOTHING
            RETURNING id
            """,
            row_id, user_id, org_id, platform_id, type_id,
            c["platform_post_id"], observed, c.get("extractor_version", "v1"),
            c.get("author_handle"), c.get("author_name"),
            c.get("text_excerpt"), c.get("url"),
            c.get("like_count"), c.get("reply_count"),
            c.get("repost_count"), c.get("view_count"),
            c.get("is_own", False),
            c.get("raw_attrs") or {},
        )
        if result is not None:
            inserted_ids.append(row_id)
        else:
            deduped += 1

    return inserted_ids, deduped


async def list_captures(
    conn: Any,
    *,
    user_id: str,
    org_id: str | None = None,
    platform: str | None = None,
    capture_type: str | None = None,
    from_dt: dt.datetime | None = None,
    to_dt: dt.datetime | None = None,
    is_own: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Return (items, total)."""
    await _ensure_dims(conn)

    wheres = ["user_id = $1"]
    params: list[Any] = [user_id]
    idx = 2

    if org_id:
        wheres.append(f"org_id = ${idx}"); params.append(org_id); idx += 1
    if platform:
        pid = _PLATFORM_IDS.get(platform)
        if pid:
            wheres.append(f"platform_id = ${idx}"); params.append(pid); idx += 1
    if capture_type:
        tid = _TYPE_IDS.get(capture_type)
        if tid:
            wheres.append(f"type_id = ${idx}"); params.append(tid); idx += 1
    if from_dt:
        ts = from_dt.replace(tzinfo=None) if from_dt.tzinfo else from_dt
        wheres.append(f"observed_at >= ${idx}"); params.append(ts); idx += 1
    if to_dt:
        ts = to_dt.replace(tzinfo=None) if to_dt.tzinfo else to_dt
        wheres.append(f"observed_at <= ${idx}"); params.append(ts); idx += 1
    if is_own is not None:
        wheres.append(f"is_own = ${idx}"); params.append(is_own); idx += 1

    where_sql = " AND ".join(wheres)
    base = f'FROM {_VIEW} WHERE {where_sql}'

    total = await conn.fetchval(f"SELECT COUNT(*) {base}", *params)
    rows = await conn.fetch(
        f"SELECT * {base} ORDER BY observed_at DESC LIMIT {limit} OFFSET {offset}",
        *params,
    )
    return [_row_to_dict(r) for r in rows], int(total)

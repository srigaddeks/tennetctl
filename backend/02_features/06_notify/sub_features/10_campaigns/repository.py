"""Repository for notify.campaigns — asyncpg raw SQL."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _parse_ts(ts: str | None) -> datetime | None:
    """Parse ISO 8601 string to datetime, or return None."""
    if ts is None:
        return None
    return datetime.fromisoformat(ts)

_FCT  = '"06_notify"."18_fct_notify_campaigns"'
_VIEW = '"06_notify"."v_notify_campaigns"'

# Campaign status IDs (mirrors 05_dim_notify_campaign_statuses seed)
STATUS_DRAFT     = 1
STATUS_SCHEDULED = 2
STATUS_RUNNING   = 3
STATUS_PAUSED    = 4
STATUS_COMPLETED = 5
STATUS_CANCELLED = 6
STATUS_FAILED    = 7


async def list_campaigns(
    conn: Any,
    *,
    org_id: str,
    status_code: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    params: list[Any] = [org_id, limit, offset]
    clauses = ["org_id = $1"]
    if status_code:
        params.append(status_code)
        clauses.append(f"status_code = ${len(params)}")
    where = " AND ".join(clauses)
    rows = await conn.fetch(
        f"SELECT * FROM {_VIEW} WHERE {where} ORDER BY created_at DESC LIMIT $2 OFFSET $3",
        *params,
    )
    return [dict(r) for r in rows]


async def get_campaign(conn: Any, campaign_id: str) -> dict | None:
    row = await conn.fetchrow(f"SELECT * FROM {_VIEW} WHERE id = $1", campaign_id)
    return dict(row) if row else None


async def create_campaign(
    conn: Any,
    *,
    campaign_id: str,
    org_id: str,
    name: str,
    template_id: str,
    channel_id: int,
    audience_query: dict,
    scheduled_at: str | None,
    throttle_per_minute: int,
    created_by: str,
) -> dict:
    parsed_ts = _parse_ts(scheduled_at)
    await conn.execute(
        f"""
        INSERT INTO {_FCT}
            (id, org_id, name, template_id, channel_id, audience_query,
             scheduled_at, throttle_per_minute, status_id, created_by, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10)
        """,
        campaign_id, org_id, name, template_id, channel_id, audience_query,
        parsed_ts, throttle_per_minute,
        STATUS_SCHEDULED if parsed_ts else STATUS_DRAFT,
        created_by,
    )
    row = await conn.fetchrow(f"SELECT * FROM {_VIEW} WHERE id = $1", campaign_id)
    return dict(row)


async def update_campaign(
    conn: Any,
    *,
    campaign_id: str,
    updated_by: str,
    name: str | None = None,
    template_id: str | None = None,
    channel_id: int | None = None,
    audience_query: dict | None = None,
    scheduled_at: str | None = None,
    throttle_per_minute: int | None = None,
    status_id: int | None = None,
) -> dict | None:
    sets = []
    params: list[Any] = [campaign_id, updated_by]

    def _add(col: str, val: Any) -> None:
        params.append(val)
        sets.append(f"{col} = ${len(params)}")

    if name is not None:
        _add("name", name)
    if template_id is not None:
        _add("template_id", template_id)
    if channel_id is not None:
        _add("channel_id", channel_id)
    if audience_query is not None:
        _add("audience_query", audience_query)
    if scheduled_at is not None:
        params.append(_parse_ts(scheduled_at))
        sets.append(f"scheduled_at = ${len(params)}")
    if throttle_per_minute is not None:
        _add("throttle_per_minute", throttle_per_minute)
    if status_id is not None:
        _add("status_id", status_id)

    if not sets:
        return await get_campaign(conn, campaign_id)

    sets.append("updated_by = $2")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    clause = ", ".join(sets)
    await conn.execute(
        f"UPDATE {_FCT} SET {clause} WHERE id = $1",
        *params,
    )
    return await get_campaign(conn, campaign_id)


async def delete_campaign(conn: Any, *, campaign_id: str, updated_by: str) -> bool:
    result = await conn.execute(
        f"UPDATE {_FCT} SET deleted_at = CURRENT_TIMESTAMP, updated_by = $2, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = $1 AND deleted_at IS NULL",
        campaign_id, updated_by,
    )
    return result == "UPDATE 1"


async def poll_scheduled_campaigns(conn: Any) -> list[dict]:
    """Return campaigns that are scheduled and due to run."""
    rows = await conn.fetch(
        f"""
        SELECT * FROM {_FCT}
        WHERE status_id = $1
          AND scheduled_at <= CURRENT_TIMESTAMP
          AND deleted_at IS NULL
        ORDER BY scheduled_at ASC
        LIMIT 10
        """,
        STATUS_SCHEDULED,
    )
    return [dict(r) for r in rows]


async def update_campaign_status(
    conn: Any,
    *,
    campaign_id: str,
    status_id: int,
) -> None:
    await conn.execute(
        f"UPDATE {_FCT} SET status_id = $2, updated_at = CURRENT_TIMESTAMP WHERE id = $1",
        campaign_id, status_id,
    )


async def get_audience_user_ids(
    conn: Any,
    *,
    org_id: str,
    account_type_codes: list[str] | None = None,
) -> list[str]:
    """
    Resolve campaign audience: active users in the org, optionally filtered by
    account type. Queries across the 03_iam schema (cross-schema read — safe
    since both schemas are in the same database).
    """
    if account_type_codes:
        rows = await conn.fetch(
            """
            SELECT u.id
            FROM "03_iam"."40_lnk_user_orgs" luo
            JOIN "03_iam"."v_users" u ON u.id = luo.user_id
            WHERE luo.org_id = $1
              AND u.is_active = TRUE
              AND u.deleted_at IS NULL
              AND u.account_type = ANY($2::text[])
            """,
            org_id, account_type_codes,
        )
    else:
        rows = await conn.fetch(
            """
            SELECT u.id
            FROM "03_iam"."40_lnk_user_orgs" luo
            JOIN "03_iam"."v_users" u ON u.id = luo.user_id
            WHERE luo.org_id = $1
              AND u.is_active = TRUE
              AND u.deleted_at IS NULL
            """,
            org_id,
        )
    return [r["id"] for r in rows]

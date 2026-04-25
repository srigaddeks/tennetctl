"""
product_ops.track — service layer.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

_core_id = import_module("backend.01_core.id")
_repo = import_module(
    "backend.02_features.10_product_ops.sub_features.01_track.repository"
)

# Sentinel for anonymous-traffic events that arrive without a session-bound org.
# Allows the public ingest endpoint to accept events from unauthenticated browser
# SDKs in single-tenant deployments. Multi-tenant deployments should pass org_id
# in the body or behind an authenticated gateway.
ANON_ORG_ID = "system"


async def track(
    conn: Any,
    *,
    event: str,
    distinct_id: str,
    org_id: str | None,
    workspace_id: str | None,
    actor_user_id: str | None,
    session_id: str | None,
    source: str,
    url: str | None,
    user_agent: str | None,
    ip_addr: str | None,
    properties: dict[str, Any],
) -> dict[str, Any]:
    return await _repo.insert_event(
        conn,
        event_id=_core_id.uuid7(),
        org_id=org_id or ANON_ORG_ID,
        workspace_id=workspace_id,
        actor_user_id=actor_user_id,
        distinct_id=distinct_id,
        event_name=event,
        session_id=session_id,
        source=source,
        url=url,
        user_agent=user_agent,
        ip_addr=ip_addr,
        properties=properties,
    )


def _decode_cursor(cursor: str | None) -> tuple[Any, str | None]:
    if not cursor:
        return None, None
    try:
        ts, eid = cursor.split("|", 1)
        return datetime.fromisoformat(ts), eid
    except Exception:
        return None, None


def _encode_cursor(created_at: datetime, event_id: str) -> str:
    return f"{created_at.isoformat()}|{event_id}"


async def list_events(
    conn: Any,
    *,
    org_id: str,
    event_name: str | None,
    distinct_id: str | None,
    actor_user_id: str | None,
    source: str | None,
    since: datetime | None,
    until: datetime | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[dict[str, Any]], str | None]:
    cursor_ts, cursor_id = _decode_cursor(cursor)
    rows = await _repo.list_events(
        conn,
        org_id=org_id,
        event_name=event_name,
        distinct_id=distinct_id,
        actor_user_id=actor_user_id,
        source=source,
        since=since,
        until=until,
        cursor_created_at=cursor_ts,
        cursor_id=cursor_id,
        limit=limit + 1,
    )
    next_cursor: str | None = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = _encode_cursor(last["created_at"], last["id"])
        rows = rows[:limit]
    return rows, next_cursor


async def counts(conn: Any, *, org_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today_start = datetime(now.year, now.month, now.day)
    last_24h = now - timedelta(hours=24)
    events_today = await _repo.count_events_since(conn, org_id=org_id, since=today_start)
    events_24h = await _repo.count_events_since(conn, org_id=org_id, since=last_24h)
    distinct_24h = await _repo.count_distinct_ids_since(conn, org_id=org_id, since=last_24h)
    dau = await _repo.count_distinct_ids_since(conn, org_id=org_id, since=today_start)
    top = await _repo.top_events_since(conn, org_id=org_id, since=last_24h, limit=10)
    return {
        "events_today": events_today,
        "events_24h": events_24h,
        "dau": dau,
        "distinct_ids_24h": distinct_24h,
        "top_events_24h": top,
    }


async def list_event_keys(conn: Any, *, org_id: str, limit: int = 200) -> list[str]:
    return await _repo.list_event_keys(conn, org_id=org_id, limit=limit)

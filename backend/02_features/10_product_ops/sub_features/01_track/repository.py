"""
product_ops.track — repository (asyncpg raw SQL).

Reads via v_product_events. Writes append rows to evt_product_events.
"""

from __future__ import annotations

from typing import Any

_TABLE = '"10_product_ops"."60_evt_product_events"'
_VIEW = '"10_product_ops"."v_product_events"'


async def insert_event(
    conn: Any,
    *,
    event_id: str,
    org_id: str,
    workspace_id: str | None,
    actor_user_id: str | None,
    distinct_id: str,
    event_name: str,
    session_id: str | None,
    source: str,
    url: str | None,
    user_agent: str | None,
    ip_addr: str | None,
    properties: dict[str, Any],
) -> dict[str, Any]:
    sql = f"""
        INSERT INTO {_TABLE}
            (id, org_id, workspace_id, actor_user_id, distinct_id, event_name,
             session_id, source, url, user_agent, ip_addr, properties)
        VALUES
            ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::inet, $12)
        RETURNING id, created_at
    """
    row = await conn.fetchrow(
        sql,
        event_id, org_id, workspace_id, actor_user_id, distinct_id, event_name,
        session_id, source, url, user_agent, ip_addr, properties,
    )
    return dict(row)


async def list_events(
    conn: Any,
    *,
    org_id: str,
    event_name: str | None,
    distinct_id: str | None,
    actor_user_id: str | None,
    source: str | None,
    since: Any,
    until: Any,
    cursor_created_at: Any,
    cursor_id: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    where = ["org_id = $1"]
    args: list[Any] = [org_id]

    def _add(clause: str, value: Any) -> None:
        args.append(value)
        where.append(clause.replace("?", f"${len(args)}"))

    if event_name:
        _add("event_name = ?", event_name)
    if distinct_id:
        _add("distinct_id = ?", distinct_id)
    if actor_user_id:
        _add("actor_user_id = ?", actor_user_id)
    if source:
        _add("source = ?", source)
    if since is not None:
        _add("created_at >= ?", since)
    if until is not None:
        _add("created_at <= ?", until)
    if cursor_created_at is not None and cursor_id is not None:
        # Tuple-based pagination on (created_at DESC, id DESC)
        args.extend([cursor_created_at, cursor_id])
        where.append(
            f"(created_at, id) < (${len(args)-1}, ${len(args)})"
        )

    args.append(limit)
    sql = f"""
        SELECT id, org_id, workspace_id, actor_user_id, distinct_id, event_name,
               session_id, source, url, user_agent, ip_addr, properties, created_at
        FROM {_VIEW}
        WHERE {' AND '.join(where)}
        ORDER BY created_at DESC, id DESC
        LIMIT ${len(args)}
    """
    rows = await conn.fetch(sql, *args)
    return [dict(r) for r in rows]


async def count_events_since(conn: Any, *, org_id: str, since: Any) -> int:
    sql = f"""
        SELECT COUNT(*) AS n
        FROM {_TABLE}
        WHERE org_id = $1 AND created_at >= $2
    """
    return int(await conn.fetchval(sql, org_id, since) or 0)


async def count_distinct_ids_since(conn: Any, *, org_id: str, since: Any) -> int:
    sql = f"""
        SELECT COUNT(DISTINCT distinct_id) AS n
        FROM {_TABLE}
        WHERE org_id = $1 AND created_at >= $2
    """
    return int(await conn.fetchval(sql, org_id, since) or 0)


async def top_events_since(
    conn: Any, *, org_id: str, since: Any, limit: int
) -> list[dict[str, Any]]:
    sql = f"""
        SELECT event_name, COUNT(*) AS n
        FROM {_TABLE}
        WHERE org_id = $1 AND created_at >= $2
        GROUP BY event_name
        ORDER BY n DESC, event_name ASC
        LIMIT $3
    """
    rows = await conn.fetch(sql, org_id, since, limit)
    return [{"event_name": r["event_name"], "count": int(r["n"])} for r in rows]


async def list_event_keys(conn: Any, *, org_id: str, limit: int) -> list[str]:
    sql = f"""
        SELECT DISTINCT event_name
        FROM {_TABLE}
        WHERE org_id = $1
        ORDER BY event_name ASC
        LIMIT $2
    """
    rows = await conn.fetch(sql, org_id, limit)
    return [r["event_name"] for r in rows]

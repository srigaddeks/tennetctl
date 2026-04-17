"""Repository for notify.subscriptions — asyncpg raw SQL."""

from __future__ import annotations

from typing import Any

_VIEW = '"06_notify"."v_notify_subscriptions"'
_FCT  = '"06_notify"."14_fct_notify_subscriptions"'


async def list_subscriptions(
    conn: Any, *, org_id: str, include_inactive: bool = False
) -> list[dict]:
    if include_inactive:
        # Read directly from fct (view filters deleted_at)
        rows = await conn.fetch(
            f'SELECT * FROM {_FCT} WHERE org_id = $1 ORDER BY created_at DESC',
            org_id,
        )
    else:
        rows = await conn.fetch(
            f'SELECT * FROM {_VIEW} WHERE org_id = $1 ORDER BY created_at DESC',
            org_id,
        )
    return [dict(r) for r in rows]


async def get_subscription(conn: Any, sub_id: str) -> dict | None:
    row = await conn.fetchrow(
        f'SELECT * FROM {_VIEW} WHERE id = $1', sub_id
    )
    return dict(row) if row else None


async def create_subscription(
    conn: Any,
    *,
    sub_id: str,
    org_id: str,
    name: str,
    event_key_pattern: str,
    template_id: str,
    channel_id: int,
    created_by: str,
) -> dict:
    await conn.execute(
        f"""
        INSERT INTO {_FCT}
            (id, org_id, name, event_key_pattern, template_id, channel_id, created_by, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
        """,
        sub_id, org_id, name, event_key_pattern, template_id, channel_id, created_by,
    )
    row = await conn.fetchrow(f'SELECT * FROM {_VIEW} WHERE id = $1', sub_id)
    return dict(row)


async def update_subscription(
    conn: Any, *, sub_id: str, updated_by: str, **fields: Any
) -> dict | None:
    allowed = {"name", "event_key_pattern", "template_id", "channel_id", "is_active"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return await get_subscription(conn, sub_id)

    set_clauses = [f"{col} = ${i+2}" for i, col in enumerate(updates)]
    set_clauses.append(f"updated_by = ${len(updates)+2}")
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params = [sub_id, *updates.values(), updated_by]

    await conn.execute(
        f"""
        UPDATE {_FCT}
        SET {', '.join(set_clauses)}
        WHERE id = $1 AND deleted_at IS NULL
        """,
        *params,
    )
    return await get_subscription(conn, sub_id)


async def delete_subscription(conn: Any, *, sub_id: str, updated_by: str) -> bool:
    result = await conn.execute(
        f"""
        UPDATE {_FCT}
        SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, updated_by = $2
        WHERE id = $1 AND deleted_at IS NULL
        """,
        sub_id, updated_by,
    )
    return result == "UPDATE 1"


async def list_active_subscriptions_all(conn: Any) -> list[dict]:
    """Return all active subscriptions across all orgs — used by the worker."""
    rows = await conn.fetch(
        f'SELECT * FROM {_VIEW} WHERE is_active = true ORDER BY created_at ASC'
    )
    return [dict(r) for r in rows]

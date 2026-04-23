"""Queue repository."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.solsocial.backend.01_core.id")

SCHEMA = '"10_solsocial"'


async def get_by_channel(conn: Any, *, channel_id: str, workspace_id: str) -> dict | None:
    row = await conn.fetchrow(
        f'SELECT * FROM {SCHEMA}.v_queues WHERE channel_id = $1 AND workspace_id = $2',
        channel_id, workspace_id,
    )
    return dict(row) if row else None


async def list_slots(conn: Any, *, queue_id: str) -> list[dict]:
    rows = await conn.fetch(
        f'SELECT * FROM {SCHEMA}."23_dtl_queue_slots" WHERE queue_id = $1 '
        'ORDER BY day_of_week, hour, minute',
        queue_id,
    )
    return [dict(r) for r in rows]


async def upsert_queue(
    conn: Any, *, channel_id: str, workspace_id: str, org_id: str, timezone: str,
    created_by: str = "sys",
) -> dict:
    existing = await get_by_channel(conn, channel_id=channel_id, workspace_id=workspace_id)
    if existing:
        await conn.execute(
            f'UPDATE {SCHEMA}."12_fct_queues" SET timezone = $1, updated_by = $2, '
            'updated_at = CURRENT_TIMESTAMP WHERE id = $3',
            timezone, created_by, existing["id"],
        )
        return await get_by_channel(conn, channel_id=channel_id, workspace_id=workspace_id) or existing
    queue_id = _id.uuid7()
    await conn.execute(
        f'INSERT INTO {SCHEMA}."12_fct_queues" '
        '(id, channel_id, workspace_id, org_id, timezone, created_by, updated_by) '
        'VALUES ($1, $2, $3, $4, $5, $6, $6)',
        queue_id, channel_id, workspace_id, org_id, timezone, created_by,
    )
    return await get_by_channel(conn, channel_id=channel_id, workspace_id=workspace_id) or {}


async def replace_slots(conn: Any, *, queue_id: str, slots: list[dict]) -> None:
    async with conn.transaction():
        await conn.execute(
            f'DELETE FROM {SCHEMA}."23_dtl_queue_slots" WHERE queue_id = $1', queue_id,
        )
        for s in slots:
            await conn.execute(
                f'INSERT INTO {SCHEMA}."23_dtl_queue_slots" '
                '(id, queue_id, day_of_week, hour, minute) '
                'VALUES ($1, $2, $3, $4, $5)',
                _id.uuid7(), queue_id, s["day_of_week"], s["hour"], s["minute"],
            )

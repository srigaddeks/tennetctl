"""asyncpg raw SQL for product_ops.destinations."""

from __future__ import annotations

from typing import Any


async def insert_destination(
    conn: Any, *,
    dest_id: str, slug: str, name: str, description: str | None,
    org_id: str, workspace_id: str, kind: str, url: str, secret: str | None,
    headers: dict, filter_rule: dict, retry_policy: dict, created_by: str,
) -> dict:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."10_fct_destinations"
            (id, slug, name, description, org_id, workspace_id,
             kind, url, secret, headers, filter_rule, retry_policy, created_by)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
        """,
        dest_id, slug, name, description, org_id, workspace_id,
        kind, url, secret, headers, filter_rule, retry_policy, created_by,
    )
    return await get_destination_by_id(conn, dest_id)


async def get_destination_by_id(conn: Any, dest_id: str) -> dict:
    row = await conn.fetchrow(
        'SELECT * FROM "10_product_ops".v_destinations WHERE id = $1', dest_id,
    )
    return dict(row) if row else {}


async def get_destination_with_secret(conn: Any, dest_id: str) -> dict | None:
    """Includes the secret — for service use only, never returned to clients."""
    row = await conn.fetchrow(
        'SELECT * FROM "10_product_ops"."10_fct_destinations" WHERE id = $1', dest_id,
    )
    return dict(row) if row else None


async def list_destinations(
    conn: Any, *, workspace_id: str,
    kind: str | None = None, limit: int = 100, offset: int = 0,
) -> tuple[list[dict], int]:
    where = ['workspace_id = $1', 'is_deleted = FALSE']
    args: list[Any] = [workspace_id]
    if kind:
        args.append(kind); where.append(f"kind = ${len(args)}")
    where_sql = " AND ".join(where)
    rows = await conn.fetch(
        f'SELECT * FROM "10_product_ops".v_destinations WHERE {where_sql} '
        f'ORDER BY created_at DESC LIMIT ${len(args)+1} OFFSET ${len(args)+2}',
        *args, limit, offset,
    )
    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "10_product_ops".v_destinations WHERE {where_sql}',
        *args,
    )
    return [dict(r) for r in rows], int(total or 0)


async def list_active_destinations_for_workspace(conn: Any, workspace_id: str) -> list[dict]:
    """Hot path — read at every ingest batch. Returns the raw fct_ rows including secret."""
    rows = await conn.fetch(
        """
        SELECT id, slug, name, kind, url, secret, headers, filter_rule, retry_policy,
               org_id, workspace_id
          FROM "10_product_ops"."10_fct_destinations"
         WHERE workspace_id = $1 AND is_active = TRUE AND deleted_at IS NULL
        """,
        workspace_id,
    )
    return [dict(r) for r in rows]


async def update_destination(conn: Any, *, dest_id: str, fields: dict) -> dict | None:
    if not fields:
        return await get_destination_by_id(conn, dest_id)
    set_parts: list[str] = []; values: list[Any] = []
    for i, (k, v) in enumerate(fields.items(), start=2):
        set_parts.append(f"{k} = ${i}"); values.append(v)
    set_parts.append("updated_at = CURRENT_TIMESTAMP")
    sql = (f'UPDATE "10_product_ops"."10_fct_destinations" '
           f'SET {", ".join(set_parts)} WHERE id = $1 RETURNING id')
    out = await conn.fetchrow(sql, dest_id, *values)
    return await get_destination_by_id(conn, dest_id) if out else None


async def soft_delete_destination(conn: Any, dest_id: str) -> bool:
    res = await conn.execute(
        'UPDATE "10_product_ops"."10_fct_destinations" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $1 AND deleted_at IS NULL',
        dest_id,
    )
    return res.endswith(" 1")


async def insert_delivery(
    conn: Any, *,
    delivery_id: str, destination_id: str, event_id: str | None,
    org_id: str, workspace_id: str, status: str, attempt: int,
    response_code: int | None, response_body: str | None,
    duration_ms: int | None, error_message: str | None, metadata: dict,
) -> str:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."60_evt_destination_deliveries"
            (id, destination_id, event_id, org_id, workspace_id,
             status, attempt, response_code, response_body, duration_ms,
             error_message, metadata)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
        """,
        delivery_id, destination_id, event_id, org_id, workspace_id,
        status, attempt, response_code, response_body, duration_ms,
        error_message, metadata,
    )
    return delivery_id


async def list_deliveries(
    conn: Any, destination_id: str, *,
    status: str | None = None, limit: int = 100, offset: int = 0,
) -> tuple[list[dict], int]:
    where = ['destination_id = $1']
    args: list[Any] = [destination_id]
    if status:
        args.append(status); where.append(f"status = ${len(args)}")
    where_sql = " AND ".join(where)
    rows = await conn.fetch(
        f'SELECT id, destination_id, event_id, status, attempt, response_code, '
        f'duration_ms, error_message, occurred_at FROM "10_product_ops"."60_evt_destination_deliveries" '
        f'WHERE {where_sql} ORDER BY occurred_at DESC '
        f'LIMIT ${len(args)+1} OFFSET ${len(args)+2}',
        *args, limit, offset,
    )
    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "10_product_ops"."60_evt_destination_deliveries" WHERE {where_sql}',
        *args,
    )
    return [dict(r) for r in rows], int(total or 0)

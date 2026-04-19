"""asyncpg raw SQL for product_ops.promos."""

from __future__ import annotations

from datetime import datetime
from typing import Any


async def insert_code(
    conn: Any, *,
    promo_id: str,
    code: str,
    org_id: str,
    workspace_id: str,
    redemption_kind: str,
    redemption_config: dict,
    description: str | None,
    max_total_uses: int | None,
    max_uses_per_visitor: int,
    starts_at: datetime | None,
    ends_at: datetime | None,
    eligibility: dict,
    created_by: str,
) -> dict:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."10_fct_promo_codes"
            (id, code, org_id, workspace_id,
             redemption_kind, redemption_config, description,
             max_total_uses, max_uses_per_visitor,
             starts_at, ends_at, eligibility, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """,
        promo_id, code, org_id, workspace_id,
        redemption_kind, redemption_config, description,
        max_total_uses, max_uses_per_visitor,
        starts_at, ends_at, eligibility, created_by,
    )
    return await get_code_by_id(conn, promo_id)


async def get_code_by_id(conn: Any, promo_id: str) -> dict:
    row = await conn.fetchrow(
        'SELECT * FROM "10_product_ops".v_promo_codes WHERE id = $1',
        promo_id,
    )
    return dict(row) if row else {}


async def get_code_by_code(conn: Any, *, workspace_id: str, code: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT * FROM "10_product_ops".v_promo_codes
         WHERE workspace_id = $1 AND code = $2 AND is_deleted = FALSE
        """,
        workspace_id, code,
    )
    return dict(row) if row else None


async def list_codes(
    conn: Any, *,
    workspace_id: str,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict], int]:
    where = ['workspace_id = $1', 'is_deleted = FALSE']
    args: list[Any] = [workspace_id]
    if status:
        args.append(status)
        where.append(f"status = ${len(args)}")
    where_sql = " AND ".join(where)
    args_paged = [*args, limit, offset]
    rows = await conn.fetch(
        f'SELECT * FROM "10_product_ops".v_promo_codes WHERE {where_sql} '
        f'ORDER BY created_at DESC LIMIT ${len(args)+1} OFFSET ${len(args)+2}',
        *args_paged,
    )
    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "10_product_ops".v_promo_codes WHERE {where_sql}',
        *args,
    )
    return [dict(r) for r in rows], int(total or 0)


async def soft_delete_code(conn: Any, promo_id: str) -> bool:
    res = await conn.execute(
        """
        UPDATE "10_product_ops"."10_fct_promo_codes"
           SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
         WHERE id = $1 AND deleted_at IS NULL
        """,
        promo_id,
    )
    return res.endswith(" 1")


async def update_code(conn: Any, *, promo_id: str, fields: dict) -> dict | None:
    if not fields:
        return await get_code_by_id(conn, promo_id)
    set_parts: list[str] = []
    values: list[Any] = []
    for i, (k, v) in enumerate(fields.items(), start=2):
        set_parts.append(f"{k} = ${i}")
        values.append(v)
    set_parts.append("updated_at = CURRENT_TIMESTAMP")
    sql = (
        f'UPDATE "10_product_ops"."10_fct_promo_codes" '
        f'SET {", ".join(set_parts)} WHERE id = $1 RETURNING id'
    )
    out = await conn.fetchrow(sql, promo_id, *values)
    if not out:
        return None
    return await get_code_by_id(conn, promo_id)


# ── Redemption ──────────────────────────────────────────────────────

async def count_redemptions_for_visitor(
    conn: Any, *, promo_code_id: str, visitor_id: str,
) -> int:
    return int(await conn.fetchval(
        """
        SELECT COUNT(*) FROM "10_product_ops"."60_evt_promo_redemptions"
         WHERE promo_code_id = $1 AND visitor_id = $2 AND outcome = 'redeemed'
        """,
        promo_code_id, visitor_id,
    ) or 0)


async def insert_redemption(
    conn: Any, *,
    redemption_id: str,
    promo_code_id: str,
    visitor_id: str | None,
    redeemer_user_id: str | None,
    org_id: str,
    workspace_id: str,
    outcome: str,
    rejection_reason: str | None,
    metadata: dict,
    occurred_at: datetime,
) -> str:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."60_evt_promo_redemptions"
            (id, promo_code_id, visitor_id, redeemer_user_id,
             org_id, workspace_id, outcome, rejection_reason, metadata, occurred_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
        redemption_id, promo_code_id, visitor_id, redeemer_user_id,
        org_id, workspace_id, outcome, rejection_reason, metadata, occurred_at,
    )
    return redemption_id

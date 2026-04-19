"""asyncpg raw SQL for product_ops.partners."""

from __future__ import annotations

from datetime import datetime
from typing import Any


async def insert_partner(
    conn: Any, *,
    partner_id: str,
    slug: str,
    display_name: str,
    contact_email: str,
    org_id: str,
    workspace_id: str,
    user_id: str | None,
    tier_id: int,
    created_by: str,
) -> dict:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."10_fct_partners"
            (id, slug, display_name, contact_email,
             org_id, workspace_id, user_id, tier_id, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        partner_id, slug, display_name, contact_email,
        org_id, workspace_id, user_id, tier_id, created_by,
    )
    return await get_partner_by_id(conn, partner_id)


async def get_partner_by_id(conn: Any, partner_id: str) -> dict:
    row = await conn.fetchrow(
        'SELECT * FROM "10_product_ops".v_partners WHERE id = $1',
        partner_id,
    )
    return dict(row) if row else {}


async def get_partner_by_slug(conn: Any, *, workspace_id: str, slug: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT * FROM "10_product_ops".v_partners
         WHERE workspace_id = $1 AND slug = $2 AND is_deleted = FALSE
        """,
        workspace_id, slug,
    )
    return dict(row) if row else None


async def list_partners(
    conn: Any, *,
    workspace_id: str,
    tier_code: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict], int]:
    where = ['workspace_id = $1', 'is_deleted = FALSE']
    args: list[Any] = [workspace_id]
    if tier_code:
        args.append(tier_code)
        where.append(f"tier_code = ${len(args)}")
    where_sql = " AND ".join(where)
    args_paged = [*args, limit, offset]
    rows = await conn.fetch(
        f'SELECT * FROM "10_product_ops".v_partners WHERE {where_sql} '
        f'ORDER BY conversion_value_cents_total DESC, created_at DESC '
        f'LIMIT ${len(args)+1} OFFSET ${len(args)+2}',
        *args_paged,
    )
    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "10_product_ops".v_partners WHERE {where_sql}',
        *args,
    )
    return [dict(r) for r in rows], int(total or 0)


async def update_partner(conn: Any, *, partner_id: str, fields: dict) -> dict | None:
    if not fields:
        return await get_partner_by_id(conn, partner_id)
    set_parts: list[str] = []
    values: list[Any] = []
    for i, (k, v) in enumerate(fields.items(), start=2):
        set_parts.append(f"{k} = ${i}")
        values.append(v)
    set_parts.append("updated_at = CURRENT_TIMESTAMP")
    sql = (
        f'UPDATE "10_product_ops"."10_fct_partners" '
        f'SET {", ".join(set_parts)} WHERE id = $1 RETURNING id'
    )
    out = await conn.fetchrow(sql, partner_id, *values)
    if not out:
        return None
    return await get_partner_by_id(conn, partner_id)


async def soft_delete_partner(conn: Any, partner_id: str) -> bool:
    res = await conn.execute(
        """
        UPDATE "10_product_ops"."10_fct_partners"
           SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
         WHERE id = $1 AND deleted_at IS NULL
        """,
        partner_id,
    )
    return res.endswith(" 1")


# ── Code linkage ────────────────────────────────────────────────────

async def link_code(
    conn: Any, *,
    link_id: str,
    partner_id: str,
    code_kind: str,
    referral_code_id: str | None,
    promo_code_id: str | None,
    payout_bp_override: int | None,
    org_id: str,
    created_by: str,
) -> dict:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."40_lnk_partner_codes"
            (id, partner_id, code_kind, referral_code_id, promo_code_id,
             payout_bp_override, org_id, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        link_id, partner_id, code_kind, referral_code_id, promo_code_id,
        payout_bp_override, org_id, created_by,
    )
    return {"link_id": link_id, "partner_id": partner_id, "code_kind": code_kind}


async def list_partner_codes(conn: Any, partner_id: str) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT lpc.id, lpc.partner_id, lpc.code_kind,
               lpc.referral_code_id, lpc.promo_code_id,
               lpc.payout_bp_override, lpc.created_at,
               -- Resolve the code string + status from whichever side is set
               COALESCE(rc.code, pc.code) AS code,
               COALESCE(NULL::text, pc.status) AS promo_status,
               COALESCE(rc.is_active, pc.is_active) AS is_active
          FROM "10_product_ops"."40_lnk_partner_codes" lpc
          LEFT JOIN "10_product_ops".v_referral_codes rc ON rc.id = lpc.referral_code_id
          LEFT JOIN "10_product_ops".v_promo_codes    pc ON pc.id = lpc.promo_code_id
         WHERE lpc.partner_id = $1
         ORDER BY lpc.created_at DESC
        """,
        partner_id,
    )
    return [dict(r) for r in rows]


async def unlink_code(conn: Any, link_id: str) -> bool:
    res = await conn.execute(
        'DELETE FROM "10_product_ops"."40_lnk_partner_codes" WHERE id = $1',
        link_id,
    )
    return res.endswith(" 1")


# ── Payouts ─────────────────────────────────────────────────────────

async def insert_payout(
    conn: Any, *,
    payout_id: str,
    partner_id: str,
    org_id: str,
    workspace_id: str,
    period_start: datetime,
    period_end: datetime,
    amount_cents: int,
    currency: str,
    status: str,
    paid_at: datetime | None,
    external_ref: str | None,
    metadata: dict,
    created_by: str,
) -> str:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."60_evt_partner_payouts"
            (id, partner_id, org_id, workspace_id,
             period_start, period_end, amount_cents, currency,
             status, paid_at, external_ref, metadata, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """,
        payout_id, partner_id, org_id, workspace_id,
        period_start, period_end, amount_cents, currency,
        status, paid_at, external_ref, metadata, created_by,
    )
    return payout_id


async def list_payouts_for_partner(conn: Any, partner_id: str, limit: int = 100) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT id, partner_id, period_start, period_end,
               amount_cents, currency, status, paid_at, external_ref,
               metadata, occurred_at, created_at
          FROM "10_product_ops"."60_evt_partner_payouts"
         WHERE partner_id = $1
         ORDER BY occurred_at DESC
         LIMIT $2
        """,
        partner_id, limit,
    )
    return [dict(r) for r in rows]

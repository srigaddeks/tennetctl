"""asyncpg raw SQL for product_ops.campaigns."""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ── Campaigns CRUD ─────────────────────────────────────────────────

async def insert_campaign(
    conn: Any, *,
    campaign_id: str,
    slug: str,
    name: str,
    description: str | None,
    org_id: str,
    workspace_id: str,
    starts_at: datetime | None,
    ends_at: datetime | None,
    audience_rule: dict,
    goals: dict,
    created_by: str,
) -> dict:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."10_fct_promo_campaigns"
            (id, slug, name, description, org_id, workspace_id,
             starts_at, ends_at, audience_rule, goals, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """,
        campaign_id, slug, name, description, org_id, workspace_id,
        starts_at, ends_at, audience_rule, goals, created_by,
    )
    return await get_campaign_by_id(conn, campaign_id)


async def get_campaign_by_id(conn: Any, campaign_id: str) -> dict:
    row = await conn.fetchrow(
        'SELECT * FROM "10_product_ops".v_promo_campaigns WHERE id = $1',
        campaign_id,
    )
    return dict(row) if row else {}


async def get_campaign_by_slug(conn: Any, *, workspace_id: str, slug: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT * FROM "10_product_ops".v_promo_campaigns
         WHERE workspace_id = $1 AND slug = $2 AND is_deleted = FALSE
        """,
        workspace_id, slug,
    )
    return dict(row) if row else None


async def list_campaigns(
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
    rows = await conn.fetch(
        f'SELECT * FROM "10_product_ops".v_promo_campaigns WHERE {where_sql} '
        f'ORDER BY created_at DESC LIMIT ${len(args)+1} OFFSET ${len(args)+2}',
        *args, limit, offset,
    )
    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "10_product_ops".v_promo_campaigns WHERE {where_sql}',
        *args,
    )
    return [dict(r) for r in rows], int(total or 0)


async def update_campaign(conn: Any, *, campaign_id: str, fields: dict) -> dict | None:
    if not fields:
        return await get_campaign_by_id(conn, campaign_id)
    set_parts: list[str] = []
    values: list[Any] = []
    for i, (k, v) in enumerate(fields.items(), start=2):
        set_parts.append(f"{k} = ${i}")
        values.append(v)
    set_parts.append("updated_at = CURRENT_TIMESTAMP")
    sql = (
        f'UPDATE "10_product_ops"."10_fct_promo_campaigns" '
        f'SET {", ".join(set_parts)} WHERE id = $1 RETURNING id'
    )
    out = await conn.fetchrow(sql, campaign_id, *values)
    if not out:
        return None
    return await get_campaign_by_id(conn, campaign_id)


async def soft_delete_campaign(conn: Any, campaign_id: str) -> bool:
    res = await conn.execute(
        """
        UPDATE "10_product_ops"."10_fct_promo_campaigns"
           SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
         WHERE id = $1 AND deleted_at IS NULL
        """,
        campaign_id,
    )
    return res.endswith(" 1")


# ── Promo linkage ───────────────────────────────────────────────────

async def link_promo(
    conn: Any, *,
    link_id: str,
    campaign_id: str,
    promo_code_id: str,
    weight: int,
    audience_rule_override: dict | None,
    org_id: str,
    created_by: str,
) -> str:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."40_lnk_campaign_promos"
            (id, campaign_id, promo_code_id, weight, audience_rule_override,
             org_id, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        link_id, campaign_id, promo_code_id, weight, audience_rule_override,
        org_id, created_by,
    )
    return link_id


async def list_campaign_promos(conn: Any, campaign_id: str) -> list[dict]:
    """Returns linked promos joined with v_promo_codes for status + caps."""
    rows = await conn.fetch(
        """
        SELECT lcp.id AS link_id, lcp.weight, lcp.audience_rule_override,
               pc.id AS promo_code_id, pc.code, pc.redemption_kind,
               pc.redemption_kind_label, pc.redemption_config,
               pc.status, pc.is_active, pc.starts_at, pc.ends_at,
               pc.max_total_uses, pc.max_uses_per_visitor,
               pc.redemption_count, pc.rejection_count,
               pc.eligibility
          FROM "10_product_ops"."40_lnk_campaign_promos" lcp
          JOIN "10_product_ops".v_promo_codes pc ON pc.id = lcp.promo_code_id
         WHERE lcp.campaign_id = $1
         ORDER BY lcp.weight DESC, lcp.created_at DESC
        """,
        campaign_id,
    )
    return [dict(r) for r in rows]


async def unlink_promo(conn: Any, link_id: str) -> bool:
    res = await conn.execute(
        'DELETE FROM "10_product_ops"."40_lnk_campaign_promos" WHERE id = $1',
        link_id,
    )
    return res.endswith(" 1")


# ── Exposure log ───────────────────────────────────────────────────

async def insert_exposure(
    conn: Any, *,
    exposure_id: str,
    campaign_id: str,
    promo_code_id: str | None,
    visitor_id: str,
    org_id: str,
    workspace_id: str,
    decision: str,
    metadata: dict,
    occurred_at: datetime,
) -> str:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."60_evt_campaign_exposures"
            (id, campaign_id, promo_code_id, visitor_id, org_id, workspace_id,
             decision, metadata, occurred_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        exposure_id, campaign_id, promo_code_id, visitor_id,
        org_id, workspace_id, decision, metadata, occurred_at,
    )
    return exposure_id

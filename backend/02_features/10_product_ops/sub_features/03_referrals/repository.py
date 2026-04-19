"""asyncpg raw SQL for product_ops.referrals."""

from __future__ import annotations

from datetime import datetime
from typing import Any


async def insert_code(
    conn: Any,
    *,
    code_id: str,
    code: str,
    referrer_user_id: str,
    org_id: str,
    workspace_id: str,
    reward_config: dict,
    created_by: str,
) -> dict:
    row = await conn.fetchrow(
        """
        INSERT INTO "10_product_ops"."10_fct_referral_codes"
            (id, code, referrer_user_id, org_id, workspace_id,
             reward_config, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """,
        code_id, code, referrer_user_id, org_id, workspace_id,
        reward_config, created_by,
    )
    return await get_code_by_id(conn, row["id"])


async def get_code_by_id(conn: Any, code_id: str) -> dict:
    row = await conn.fetchrow(
        'SELECT * FROM "10_product_ops".v_referral_codes WHERE id = $1',
        code_id,
    )
    return dict(row) if row else {}


async def get_code_by_code(conn: Any, *, workspace_id: str, code: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT * FROM "10_product_ops".v_referral_codes
         WHERE workspace_id = $1 AND code = $2 AND is_deleted = FALSE AND is_active = TRUE
        """,
        workspace_id, code,
    )
    return dict(row) if row else None


async def list_codes(
    conn: Any, *, workspace_id: str, limit: int = 100, offset: int = 0,
) -> tuple[list[dict], int]:
    rows = await conn.fetch(
        """
        SELECT * FROM "10_product_ops".v_referral_codes
         WHERE workspace_id = $1 AND is_deleted = FALSE
         ORDER BY created_at DESC
         LIMIT $2 OFFSET $3
        """,
        workspace_id, limit, offset,
    )
    total = await conn.fetchval(
        'SELECT COUNT(*) FROM "10_product_ops".v_referral_codes '
        'WHERE workspace_id = $1 AND is_deleted = FALSE',
        workspace_id,
    )
    return [dict(r) for r in rows], int(total or 0)


async def soft_delete_code(conn: Any, code_id: str) -> bool:
    res = await conn.execute(
        """
        UPDATE "10_product_ops"."10_fct_referral_codes"
           SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
         WHERE id = $1 AND deleted_at IS NULL
        """,
        code_id,
    )
    return res.endswith(" 1")


async def insert_conversion(
    conn: Any,
    *,
    conv_id: str,
    referral_code_id: str,
    visitor_id: str,
    converted_user_id: str | None,
    org_id: str,
    workspace_id: str,
    conversion_kind: str,
    conversion_value_cents: int | None,
    metadata: dict,
    occurred_at: datetime,
) -> str:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."60_evt_referral_conversions"
            (id, referral_code_id, visitor_id, converted_user_id,
             org_id, workspace_id,
             conversion_kind, conversion_value_cents, metadata, occurred_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
        conv_id, referral_code_id, visitor_id, converted_user_id,
        org_id, workspace_id, conversion_kind, conversion_value_cents,
        metadata, occurred_at,
    )
    return conv_id

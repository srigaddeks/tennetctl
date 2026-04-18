"""iam.impersonation — asyncpg repository."""

from __future__ import annotations

from typing import Any


async def insert_impersonation(
    conn: Any, *, id: str, session_id: str, impersonator_user_id: str,
    impersonated_user_id: str, org_id: str, created_by: str,
) -> dict:
    row = await conn.fetchrow(
        'INSERT INTO "03_iam"."45_lnk_impersonations" '
        '(id, session_id, impersonator_user_id, impersonated_user_id, org_id, created_by) '
        'VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
        id, session_id, impersonator_user_id, impersonated_user_id, org_id, created_by,
    )
    return dict(row)


async def get_by_session_id(conn: Any, *, session_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT * FROM "03_iam"."45_lnk_impersonations" WHERE session_id = $1',
        session_id,
    )
    return dict(row) if row else None


async def get_active_by_session_id(conn: Any, *, session_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT * FROM "03_iam"."45_lnk_impersonations" WHERE session_id = $1 AND ended_at IS NULL',
        session_id,
    )
    return dict(row) if row else None


async def end_impersonation(conn: Any, *, impersonation_id: str) -> None:
    await conn.execute(
        'UPDATE "03_iam"."45_lnk_impersonations" SET ended_at = CURRENT_TIMESTAMP WHERE id = $1',
        impersonation_id,
    )

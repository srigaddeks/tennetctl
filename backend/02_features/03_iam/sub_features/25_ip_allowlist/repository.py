"""iam.ip_allowlist — asyncpg repository."""

from __future__ import annotations

from typing import Any


async def list_entries(conn: Any, org_id: str) -> list[dict]:
    rows = await conn.fetch(
        'SELECT * FROM "03_iam"."46_lnk_org_ip_allowlist" WHERE org_id = $1 ORDER BY created_at',
        org_id,
    )
    return [dict(r) for r in rows]


async def insert_entry(conn: Any, *, id: str, org_id: str, cidr: str, label: str, created_by: str) -> dict:
    row = await conn.fetchrow(
        'INSERT INTO "03_iam"."46_lnk_org_ip_allowlist" (id, org_id, cidr, label, created_by) '
        'VALUES ($1, $2, $3, $4, $5) RETURNING *',
        id, org_id, cidr, label, created_by,
    )
    return dict(row)


async def delete_entry(conn: Any, *, entry_id: str, org_id: str) -> bool:
    result = await conn.execute(
        'DELETE FROM "03_iam"."46_lnk_org_ip_allowlist" WHERE id = $1 AND org_id = $2',
        entry_id, org_id,
    )
    return result != "DELETE 0"


async def get_cidrs_for_org(conn: Any, org_id: str) -> list[str]:
    rows = await conn.fetch(
        'SELECT cidr FROM "03_iam"."46_lnk_org_ip_allowlist" WHERE org_id = $1',
        org_id,
    )
    return [r["cidr"] for r in rows]

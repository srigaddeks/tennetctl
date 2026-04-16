"""
iam.memberships — asyncpg repository for lnk_user_orgs + lnk_user_workspaces.

Lnk rows are immutable (no updated_at, no deleted_at). Revoke = hard DELETE.
"""

from __future__ import annotations

from typing import Any


# ── Org memberships ─────────────────────────────────────────────────

async def get_org_membership_by_id(conn: Any, membership_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, user_id, org_id, created_by, created_at '
        'FROM "03_iam"."40_lnk_user_orgs" WHERE id = $1',
        membership_id,
    )
    return dict(row) if row else None


async def get_org_membership_by_pair(
    conn: Any, user_id: str, org_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, user_id, org_id, created_by, created_at '
        'FROM "03_iam"."40_lnk_user_orgs" '
        'WHERE user_id = $1 AND org_id = $2',
        user_id,
        org_id,
    )
    return dict(row) if row else None


async def list_org_memberships(
    conn: Any,
    *,
    limit: int,
    offset: int,
    user_id: str | None = None,
    org_id: str | None = None,
) -> tuple[list[dict], int]:
    where: list[str] = []
    params: list[Any] = []
    if user_id is not None:
        params.append(user_id)
        where.append(f"user_id = ${len(params)}")
    if org_id is not None:
        params.append(org_id)
        where.append(f"org_id = ${len(params)}")
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "03_iam"."40_lnk_user_orgs" {where_sql}',
        *params,
    )
    params_page = [*params, limit, offset]
    limit_idx = len(params_page) - 1
    offset_idx = len(params_page)
    rows = await conn.fetch(
        f'SELECT id, user_id, org_id, created_by, created_at '
        f'FROM "03_iam"."40_lnk_user_orgs" '
        f'{where_sql} '
        f'ORDER BY created_at DESC, id DESC '
        f'LIMIT ${limit_idx} OFFSET ${offset_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def insert_org_membership(
    conn: Any,
    *,
    id: str,
    user_id: str,
    org_id: str,
    created_by: str,
) -> None:
    await conn.execute(
        'INSERT INTO "03_iam"."40_lnk_user_orgs" (id, user_id, org_id, created_by) '
        'VALUES ($1, $2, $3, $4)',
        id, user_id, org_id, created_by,
    )


async def delete_org_membership(conn: Any, membership_id: str) -> bool:
    result = await conn.execute(
        'DELETE FROM "03_iam"."40_lnk_user_orgs" WHERE id = $1',
        membership_id,
    )
    return result.endswith(" 1")


# ── Workspace memberships ───────────────────────────────────────────

async def get_workspace_membership_by_id(conn: Any, membership_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, user_id, workspace_id, org_id, created_by, created_at '
        'FROM "03_iam"."41_lnk_user_workspaces" WHERE id = $1',
        membership_id,
    )
    return dict(row) if row else None


async def get_workspace_membership_by_pair(
    conn: Any, user_id: str, workspace_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, user_id, workspace_id, org_id, created_by, created_at '
        'FROM "03_iam"."41_lnk_user_workspaces" '
        'WHERE user_id = $1 AND workspace_id = $2',
        user_id,
        workspace_id,
    )
    return dict(row) if row else None


async def list_workspace_memberships(
    conn: Any,
    *,
    limit: int,
    offset: int,
    user_id: str | None = None,
    workspace_id: str | None = None,
    org_id: str | None = None,
) -> tuple[list[dict], int]:
    where: list[str] = []
    params: list[Any] = []
    if user_id is not None:
        params.append(user_id)
        where.append(f"user_id = ${len(params)}")
    if workspace_id is not None:
        params.append(workspace_id)
        where.append(f"workspace_id = ${len(params)}")
    if org_id is not None:
        params.append(org_id)
        where.append(f"org_id = ${len(params)}")
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "03_iam"."41_lnk_user_workspaces" {where_sql}',
        *params,
    )
    params_page = [*params, limit, offset]
    limit_idx = len(params_page) - 1
    offset_idx = len(params_page)
    rows = await conn.fetch(
        f'SELECT id, user_id, workspace_id, org_id, created_by, created_at '
        f'FROM "03_iam"."41_lnk_user_workspaces" '
        f'{where_sql} '
        f'ORDER BY created_at DESC, id DESC '
        f'LIMIT ${limit_idx} OFFSET ${offset_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def insert_workspace_membership(
    conn: Any,
    *,
    id: str,
    user_id: str,
    workspace_id: str,
    org_id: str,
    created_by: str,
) -> None:
    await conn.execute(
        'INSERT INTO "03_iam"."41_lnk_user_workspaces" '
        '    (id, user_id, workspace_id, org_id, created_by) '
        'VALUES ($1, $2, $3, $4, $5)',
        id, user_id, workspace_id, org_id, created_by,
    )


async def delete_workspace_membership(conn: Any, membership_id: str) -> bool:
    result = await conn.execute(
        'DELETE FROM "03_iam"."41_lnk_user_workspaces" WHERE id = $1',
        membership_id,
    )
    return result.endswith(" 1")

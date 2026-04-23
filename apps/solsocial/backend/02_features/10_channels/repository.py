"""Channel repository — raw asyncpg against the solsocial schema."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.solsocial.backend.01_core.id")

SCHEMA = '"10_solsocial"'


async def list_for_workspace(conn: Any, *, workspace_id: str, limit: int, offset: int) -> list[dict]:
    rows = await conn.fetch(
        f'SELECT * FROM {SCHEMA}.v_channels WHERE workspace_id = $1 '
        'ORDER BY created_at DESC LIMIT $2 OFFSET $3',
        workspace_id, limit, offset,
    )
    return [dict(r) for r in rows]


async def get(conn: Any, *, channel_id: str, workspace_id: str) -> dict | None:
    row = await conn.fetchrow(
        f'SELECT * FROM {SCHEMA}.v_channels WHERE id = $1 AND workspace_id = $2',
        channel_id, workspace_id,
    )
    return dict(row) if row else None


async def get_by_external_id(
    conn: Any, *, workspace_id: str, provider_code: str, external_id: str,
) -> dict | None:
    row = await conn.fetchrow(
        f'SELECT * FROM {SCHEMA}.v_channels '
        'WHERE workspace_id = $1 AND provider_code = $2 AND external_id = $3',
        workspace_id, provider_code, external_id,
    )
    return dict(row) if row else None


async def insert(
    conn: Any,
    *,
    channel_id: str | None = None,
    org_id: str,
    workspace_id: str,
    provider_id: int,
    handle: str,
    display_name: str | None,
    avatar_url: str | None,
    external_id: str | None,
    vault_key: str,
    created_by: str,
) -> dict:
    channel_id = channel_id or _id.uuid7()
    async with conn.transaction():
        await conn.execute(
            f'INSERT INTO {SCHEMA}."10_fct_channels" '
            '(id, org_id, workspace_id, provider_id, created_by, updated_by) '
            'VALUES ($1, $2, $3, $4, $5, $5)',
            channel_id, org_id, workspace_id, provider_id, created_by,
        )
        await conn.execute(
            f'INSERT INTO {SCHEMA}."20_dtl_channel_meta" '
            '(channel_id, handle, display_name, avatar_url, external_id, vault_key) '
            'VALUES ($1, $2, $3, $4, $5, $6)',
            channel_id, handle, display_name, avatar_url, external_id, vault_key,
        )
    row = await conn.fetchrow(
        f'SELECT * FROM {SCHEMA}.v_channels WHERE id = $1', channel_id,
    )
    return dict(row) if row else {}


async def soft_delete(conn: Any, *, channel_id: str, workspace_id: str) -> bool:
    result = await conn.execute(
        f'UPDATE {SCHEMA}."10_fct_channels" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $1 AND workspace_id = $2 AND deleted_at IS NULL',
        channel_id, workspace_id,
    )
    return result.endswith(" 1")


async def resolve_provider_id(conn: Any, code: str) -> int | None:
    row = await conn.fetchrow(
        f'SELECT id FROM {SCHEMA}."01_dim_channel_providers" WHERE code = $1', code,
    )
    return int(row["id"]) if row else None


async def update_meta(
    conn: Any,
    *,
    channel_id: str,
    display_name: str | None,
    avatar_url: str | None,
) -> None:
    sets = []
    params: list[Any] = []
    if display_name is not None:
        params.append(display_name)
        sets.append(f"display_name = ${len(params)}")
    if avatar_url is not None:
        params.append(avatar_url)
        sets.append(f"avatar_url = ${len(params)}")
    if not sets:
        return
    params.append(channel_id)
    await conn.execute(
        f'UPDATE {SCHEMA}."20_dtl_channel_meta" SET {", ".join(sets)} '
        f'WHERE channel_id = ${len(params)}',
        *params,
    )
    await conn.execute(
        f'UPDATE {SCHEMA}."10_fct_channels" SET updated_at = CURRENT_TIMESTAMP WHERE id = $1',
        channel_id,
    )

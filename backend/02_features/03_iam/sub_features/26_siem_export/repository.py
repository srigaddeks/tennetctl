"""iam.siem_export — asyncpg repository."""

from __future__ import annotations

from typing import Any

_TABLE = '"03_iam"."47_fct_siem_destinations"'


async def insert_destination(
    conn: Any,
    *,
    id: str,
    org_id: str,
    kind: str,
    label: str,
    config_jsonb: dict,
    credentials_vault_key: str | None,
    created_by: str,
) -> dict:
    row = await conn.fetchrow(
        f'INSERT INTO {_TABLE} '
        f'    (id, org_id, kind, label, config_jsonb, credentials_vault_key, created_by, updated_by) '
        f'VALUES ($1, $2, $3, $4, $5, $6, $7, $7) '
        f'RETURNING id, org_id, kind, label, config_jsonb, is_active, '
        f'          last_cursor, last_exported_at, failure_count, created_at, updated_at',
        id, org_id, kind, label, config_jsonb, credentials_vault_key, created_by,
    )
    return dict(row)


async def list_destinations(conn: Any, org_id: str) -> list[dict]:
    rows = await conn.fetch(
        f'SELECT id, org_id, kind, label, config_jsonb, is_active, '
        f'       last_cursor, last_exported_at, failure_count, created_at, updated_at '
        f'FROM {_TABLE} WHERE org_id = $1 AND deleted_at IS NULL '
        f'ORDER BY created_at DESC',
        org_id,
    )
    return [dict(r) for r in rows]


async def get_destination(conn: Any, dest_id: str, org_id: str) -> dict | None:
    row = await conn.fetchrow(
        f'SELECT id, org_id, kind, label, config_jsonb, credentials_vault_key, '
        f'       is_active, last_cursor, last_exported_at, failure_count, created_at, updated_at '
        f'FROM {_TABLE} WHERE id = $1 AND org_id = $2 AND deleted_at IS NULL',
        dest_id, org_id,
    )
    return dict(row) if row else None


async def update_destination(
    conn: Any,
    *,
    dest_id: str,
    org_id: str,
    label: str | None = None,
    config_jsonb: dict | None = None,
    is_active: bool | None = None,
    updated_by: str,
) -> dict | None:
    sets = ["updated_by = $3", "updated_at = CURRENT_TIMESTAMP"]
    params: list[Any] = [dest_id, org_id, updated_by]
    if label is not None:
        params.append(label)
        sets.append(f"label = ${len(params)}")
    if config_jsonb is not None:
        params.append(config_jsonb)
        sets.append(f"config_jsonb = ${len(params)}")
    if is_active is not None:
        params.append(is_active)
        sets.append(f"is_active = ${len(params)}")
    row = await conn.fetchrow(
        f'UPDATE {_TABLE} SET {", ".join(sets)} '
        f'WHERE id = $1 AND org_id = $2 AND deleted_at IS NULL '
        f'RETURNING id, org_id, kind, label, config_jsonb, is_active, '
        f'          last_cursor, last_exported_at, failure_count, created_at, updated_at',
        *params,
    )
    return dict(row) if row else None


async def soft_delete_destination(conn: Any, *, dest_id: str, org_id: str) -> bool:
    result = await conn.execute(
        f'UPDATE {_TABLE} SET deleted_at = CURRENT_TIMESTAMP '
        f'WHERE id = $1 AND org_id = $2 AND deleted_at IS NULL',
        dest_id, org_id,
    )
    return result.endswith(" 1")


async def list_active_destinations(conn: Any) -> list[dict]:
    """All active destinations across all orgs — for the SIEM worker."""
    rows = await conn.fetch(
        f'SELECT id, org_id, kind, label, config_jsonb, credentials_vault_key, '
        f'       last_cursor, failure_count '
        f'FROM {_TABLE} WHERE is_active = TRUE AND deleted_at IS NULL',
    )
    return [dict(r) for r in rows]


async def advance_cursor(
    conn: Any,
    *,
    dest_id: str,
    cursor: int,
    success: bool,
) -> None:
    if success:
        await conn.execute(
            f'UPDATE {_TABLE} SET last_cursor = $1, last_exported_at = CURRENT_TIMESTAMP, '
            f'    failure_count = 0, updated_at = CURRENT_TIMESTAMP '
            f'WHERE id = $2',
            cursor, dest_id,
        )
    else:
        await conn.execute(
            f'UPDATE {_TABLE} SET failure_count = failure_count + 1, '
            f'    updated_at = CURRENT_TIMESTAMP '
            f'WHERE id = $1',
            dest_id,
        )

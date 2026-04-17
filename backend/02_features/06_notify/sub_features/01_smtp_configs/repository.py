"""Repository for notify.smtp_configs — raw asyncpg SQL, reads v_notify_smtp_configs."""

from __future__ import annotations

from typing import Any


async def list_smtp_configs(conn: Any, *, org_id: str) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT id, org_id, key, label, host, port, tls, username, auth_vault_key,
               is_active, created_by, updated_by, created_at, updated_at
        FROM "06_notify"."v_notify_smtp_configs"
        WHERE org_id = $1
        ORDER BY created_at DESC
        """,
        org_id,
    )
    return [dict(r) for r in rows]


async def get_smtp_config(conn: Any, *, config_id: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT id, org_id, key, label, host, port, tls, username, auth_vault_key,
               is_active, created_by, updated_by, created_at, updated_at
        FROM "06_notify"."v_notify_smtp_configs"
        WHERE id = $1
        """,
        config_id,
    )
    return dict(row) if row else None


async def get_smtp_config_by_key(conn: Any, *, org_id: str, key: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT id, org_id, key, label, host, port, tls, username, auth_vault_key,
               is_active, created_by, updated_by, created_at, updated_at
        FROM "06_notify"."v_notify_smtp_configs"
        WHERE org_id = $1 AND key = $2
        """,
        org_id,
        key,
    )
    return dict(row) if row else None


async def create_smtp_config(
    conn: Any,
    *,
    config_id: str,
    org_id: str,
    key: str,
    label: str,
    host: str,
    port: int,
    tls: bool,
    username: str,
    auth_vault_key: str,
    created_by: str,
) -> dict:
    row = await conn.fetchrow(
        """
        INSERT INTO "06_notify"."10_fct_notify_smtp_configs"
            (id, org_id, key, label, host, port, tls, username, auth_vault_key,
             created_by, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10)
        RETURNING id, org_id, key, label, host, port, tls, username, auth_vault_key,
                  is_active, created_by, updated_by, created_at, updated_at
        """,
        config_id, org_id, key, label, host, port, tls, username, auth_vault_key, created_by,
    )
    return dict(row)


async def update_smtp_config(
    conn: Any,
    *,
    config_id: str,
    updated_by: str,
    **fields: Any,
) -> dict | None:
    allowed = {"label", "host", "port", "tls", "username", "auth_vault_key", "is_active"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return await get_smtp_config(conn, config_id=config_id)

    set_clauses = [f"{col} = ${i+2}" for i, col in enumerate(updates)]
    set_clauses.append(f"updated_by = ${len(updates)+2}")
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params = [config_id, *updates.values(), updated_by]

    row = await conn.fetchrow(
        f"""
        UPDATE "06_notify"."10_fct_notify_smtp_configs"
        SET {', '.join(set_clauses)}
        WHERE id = $1 AND deleted_at IS NULL
        RETURNING id, org_id, key, label, host, port, tls, username, auth_vault_key,
                  is_active, created_by, updated_by, created_at, updated_at
        """,
        *params,
    )
    return dict(row) if row else None


async def delete_smtp_config(conn: Any, *, config_id: str, updated_by: str) -> bool:
    result = await conn.execute(
        """
        UPDATE "06_notify"."10_fct_notify_smtp_configs"
        SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, updated_by = $2
        WHERE id = $1 AND deleted_at IS NULL
        """,
        config_id,
        updated_by,
    )
    return result == "UPDATE 1"

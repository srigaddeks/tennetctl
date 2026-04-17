"""Repository for notify.template_groups."""

from __future__ import annotations

from typing import Any


async def list_template_groups(conn: Any, *, org_id: str) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT id, org_id, key, label, category_id, category_code, category_label,
               smtp_config_id, smtp_config_key, is_active,
               created_by, updated_by, created_at, updated_at
        FROM "06_notify"."v_notify_template_groups"
        WHERE org_id = $1
        ORDER BY created_at DESC
        """,
        org_id,
    )
    return [dict(r) for r in rows]


async def get_template_group(conn: Any, *, group_id: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT id, org_id, key, label, category_id, category_code, category_label,
               smtp_config_id, smtp_config_key, is_active,
               created_by, updated_by, created_at, updated_at
        FROM "06_notify"."v_notify_template_groups"
        WHERE id = $1
        """,
        group_id,
    )
    return dict(row) if row else None


async def create_template_group(
    conn: Any,
    *,
    group_id: str,
    org_id: str,
    key: str,
    label: str,
    category_id: int,
    smtp_config_id: str | None,
    created_by: str,
) -> dict:
    await conn.execute(
        """
        INSERT INTO "06_notify"."11_fct_notify_template_groups"
            (id, org_id, key, label, category_id, smtp_config_id, created_by, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
        """,
        group_id, org_id, key, label, category_id, smtp_config_id, created_by,
    )
    return await get_template_group(conn, group_id=group_id)


async def update_template_group(
    conn: Any,
    *,
    group_id: str,
    updated_by: str,
    **fields: Any,
) -> dict | None:
    allowed = {"label", "category_id", "smtp_config_id", "is_active"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return await get_template_group(conn, group_id=group_id)

    set_clauses = [f"{col} = ${i+2}" for i, col in enumerate(updates)]
    set_clauses.append(f"updated_by = ${len(updates)+2}")
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params = [group_id, *updates.values(), updated_by]

    await conn.execute(
        f"""
        UPDATE "06_notify"."11_fct_notify_template_groups"
        SET {', '.join(set_clauses)}
        WHERE id = $1 AND deleted_at IS NULL
        """,
        *params,
    )
    return await get_template_group(conn, group_id=group_id)


async def delete_template_group(conn: Any, *, group_id: str, updated_by: str) -> bool:
    result = await conn.execute(
        """
        UPDATE "06_notify"."11_fct_notify_template_groups"
        SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, updated_by = $2
        WHERE id = $1 AND deleted_at IS NULL
        """,
        group_id,
        updated_by,
    )
    return result == "UPDATE 1"

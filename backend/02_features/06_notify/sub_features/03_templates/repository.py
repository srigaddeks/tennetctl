"""Repository for notify.templates — raw asyncpg SQL."""

from __future__ import annotations

import json
from typing import Any


async def list_templates(conn: Any, *, org_id: str) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT id, org_id, key, group_id, group_key, category_id, category_code,
               category_label, subject, reply_to, priority_id, priority_code,
               priority_label, is_active, created_by, updated_by, created_at, updated_at,
               bodies
        FROM "06_notify"."v_notify_templates"
        WHERE org_id = $1
        ORDER BY created_at DESC
        """,
        org_id,
    )
    return [_row_to_dict(r) for r in rows]


async def get_template(conn: Any, *, template_id: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT id, org_id, key, group_id, group_key, category_id, category_code,
               category_label, subject, reply_to, priority_id, priority_code,
               priority_label, is_active, created_by, updated_by, created_at, updated_at,
               bodies
        FROM "06_notify"."v_notify_templates"
        WHERE id = $1
        """,
        template_id,
    )
    return _row_to_dict(row) if row else None


async def get_template_by_key(conn: Any, *, org_id: str, key: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT id, org_id, key, group_id, group_key, category_id, category_code,
               category_label, subject, reply_to, priority_id, priority_code,
               priority_label, is_active, created_by, updated_by, created_at, updated_at,
               bodies
        FROM "06_notify"."v_notify_templates"
        WHERE org_id = $1 AND key = $2
        """,
        org_id,
        key,
    )
    return _row_to_dict(row) if row else None


async def create_template(
    conn: Any,
    *,
    template_id: str,
    org_id: str,
    key: str,
    group_id: str,
    subject: str,
    reply_to: str | None,
    priority_id: int,
    created_by: str,
) -> str:
    """Insert template fct row, return id."""
    await conn.execute(
        """
        INSERT INTO "06_notify"."12_fct_notify_templates"
            (id, org_id, key, group_id, subject, reply_to, priority_id, created_by, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)
        """,
        template_id, org_id, key, group_id, subject, reply_to, priority_id, created_by,
    )
    return template_id


async def update_template(
    conn: Any,
    *,
    template_id: str,
    updated_by: str,
    **fields: Any,
) -> dict | None:
    allowed = {"subject", "reply_to", "priority_id", "group_id", "is_active"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return await get_template(conn, template_id=template_id)

    set_clauses = [f"{col} = ${i+2}" for i, col in enumerate(updates)]
    set_clauses.append(f"updated_by = ${len(updates)+2}")
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params = [template_id, *updates.values(), updated_by]

    await conn.execute(
        f"""
        UPDATE "06_notify"."12_fct_notify_templates"
        SET {', '.join(set_clauses)}
        WHERE id = $1 AND deleted_at IS NULL
        """,
        *params,
    )
    return await get_template(conn, template_id=template_id)


async def delete_template(conn: Any, *, template_id: str, updated_by: str) -> bool:
    result = await conn.execute(
        """
        UPDATE "06_notify"."12_fct_notify_templates"
        SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, updated_by = $2
        WHERE id = $1 AND deleted_at IS NULL
        """,
        template_id,
        updated_by,
    )
    return result == "UPDATE 1"


async def upsert_bodies(
    conn: Any,
    *,
    template_id: str,
    body_id_fn: Any,
    bodies: list[dict],
) -> None:
    """Upsert per-channel body rows (INSERT ... ON CONFLICT DO UPDATE)."""
    for b in bodies:
        body_id = body_id_fn()
        await conn.execute(
            """
            INSERT INTO "06_notify"."20_dtl_notify_template_bodies"
                (id, template_id, channel_id, body_html, body_text, preheader)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (template_id, channel_id) DO UPDATE
                SET body_html  = EXCLUDED.body_html,
                    body_text  = EXCLUDED.body_text,
                    preheader  = EXCLUDED.preheader,
                    updated_at = CURRENT_TIMESTAMP
            """,
            body_id,
            template_id,
            b["channel_id"],
            b["body_html"],
            b.get("body_text", ""),
            b.get("preheader"),
        )


def _row_to_dict(row: Any) -> dict:
    d = dict(row)
    # asyncpg returns json_agg as a string; parse it
    if isinstance(d.get("bodies"), str):
        d["bodies"] = json.loads(d["bodies"])
    elif d.get("bodies") is None:
        d["bodies"] = []
    return d

"""asyncpg raw SQL for product_ops.links."""

from __future__ import annotations

from typing import Any


async def insert_short_link(
    conn: Any,
    *,
    link_id: str,
    slug: str,
    target_url: str,
    org_id: str,
    workspace_id: str,
    created_by: str,
    utm_source_id: int | None,
    utm_medium: str | None,
    utm_campaign: str | None,
    utm_term: str | None,
    utm_content: str | None,
) -> dict:
    row = await conn.fetchrow(
        """
        INSERT INTO "10_product_ops"."10_fct_short_links"
            (id, slug, target_url, org_id, workspace_id, created_by,
             utm_source_id, utm_medium, utm_campaign, utm_term, utm_content)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING id, slug, target_url, org_id, workspace_id,
                  utm_source_id, utm_medium, utm_campaign, utm_term, utm_content,
                  is_active, deleted_at, created_by, created_at, updated_at
        """,
        link_id, slug, target_url, org_id, workspace_id, created_by,
        utm_source_id, utm_medium, utm_campaign, utm_term, utm_content,
    )
    return dict(row)


async def get_short_link_by_slug(
    conn: Any, *, workspace_id: str, slug: str,
) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT id, slug, target_url, org_id, workspace_id,
               utm_source, utm_medium, utm_campaign, utm_term, utm_content,
               is_active, is_deleted, deleted_at, created_by, created_at, updated_at
          FROM "10_product_ops".v_short_links
         WHERE workspace_id = $1
           AND slug = $2
           AND is_deleted = FALSE
           AND is_active = TRUE
        """,
        workspace_id, slug,
    )
    return dict(row) if row else None


async def get_short_link_by_id(conn: Any, link_id: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT * FROM "10_product_ops".v_short_links WHERE id = $1
        """,
        link_id,
    )
    return dict(row) if row else None


async def list_short_links(
    conn: Any,
    *,
    workspace_id: str,
    include_deleted: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict], int]:
    where = "workspace_id = $1"
    if not include_deleted:
        where += " AND is_deleted = FALSE"

    rows = await conn.fetch(
        f"""
        SELECT * FROM "10_product_ops".v_short_links
         WHERE {where}
         ORDER BY created_at DESC
         LIMIT $2 OFFSET $3
        """,
        workspace_id, limit, offset,
    )
    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "10_product_ops".v_short_links WHERE {where}',
        workspace_id,
    )
    return [dict(r) for r in rows], int(total or 0)


async def update_short_link(
    conn: Any, *, link_id: str, fields: dict,
) -> dict | None:
    if not fields:
        return await get_short_link_by_id(conn, link_id)
    set_parts: list[str] = []
    values: list[Any] = []
    for i, (k, v) in enumerate(fields.items(), start=2):
        set_parts.append(f"{k} = ${i}")
        values.append(v)
    set_parts.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"""
        UPDATE "10_product_ops"."10_fct_short_links"
           SET {", ".join(set_parts)}
         WHERE id = $1
        RETURNING id
    """
    out = await conn.fetchrow(sql, link_id, *values)
    if not out:
        return None
    return await get_short_link_by_id(conn, link_id)


async def soft_delete_short_link(conn: Any, link_id: str) -> bool:
    res = await conn.execute(
        """
        UPDATE "10_product_ops"."10_fct_short_links"
           SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
         WHERE id = $1 AND deleted_at IS NULL
        """,
        link_id,
    )
    return res.endswith(" 1")

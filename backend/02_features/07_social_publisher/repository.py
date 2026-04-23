"""
social_publisher — asyncpg repository.

Reads go through "07_social".v_social_accounts and "07_social".v_posts views.
Writes go to raw fct_* tables.
"""

from __future__ import annotations

from typing import Any


# ── Social accounts ──────────────────────────────────────────────────────────

async def create_social_account(
    conn: Any,
    *,
    id: str,
    org_id: str,
    workspace_id: str | None,
    platform_id: int,
    account_name: str,
    account_handle: str | None,
    account_id_on_platform: str | None,
    vault_key: str,
    created_by: str,
) -> dict:
    row = await conn.fetchrow(
        """
        INSERT INTO "07_social"."10_fct_social_accounts"
          (id, org_id, workspace_id, platform_id, account_name, account_handle,
           account_id_on_platform, vault_key, created_by, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)
        RETURNING id
        """,
        id, org_id, workspace_id, platform_id, account_name, account_handle,
        account_id_on_platform, vault_key, created_by,
    )
    # Return from the view so platform label and char_limit are included
    return await _get_account_from_view(conn, account_id=row["id"])


async def _get_account_from_view(conn: Any, *, account_id: str) -> dict:
    row = await conn.fetchrow(
        'SELECT * FROM "07_social"."v_social_accounts" WHERE id = $1',
        account_id,
    )
    return dict(row) if row else {}


async def list_social_accounts(conn: Any, *, org_id: str) -> list[dict]:
    rows = await conn.fetch(
        'SELECT * FROM "07_social"."v_social_accounts" WHERE org_id = $1 ORDER BY created_at',
        org_id,
    )
    return [dict(r) for r in rows]


async def get_social_account(conn: Any, *, account_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT * FROM "07_social"."v_social_accounts" WHERE id = $1',
        account_id,
    )
    return dict(row) if row else None


async def delete_social_account(conn: Any, *, account_id: str, deleted_by: str) -> None:
    await conn.execute(
        """
        UPDATE "07_social"."10_fct_social_accounts"
        SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP,
            updated_by = $2
        WHERE id = $1 AND deleted_at IS NULL
        """,
        account_id, deleted_by,
    )


async def get_platform_id(conn: Any, *, platform_code: str) -> int | None:
    row = await conn.fetchrow(
        'SELECT id FROM "07_social"."01_dim_platforms" WHERE code = $1',
        platform_code,
    )
    return int(row["id"]) if row else None


# ── Posts ────────────────────────────────────────────────────────────────────

async def create_post(
    conn: Any,
    *,
    id: str,
    org_id: str,
    workspace_id: str | None,
    content_text: str,
    media_urls: list,
    first_comment: str | None,
    scheduled_at: Any,
    status_id: int,
    author_user_id: str | None,
    created_by: str,
) -> dict:
    await conn.execute(
        """
        INSERT INTO "07_social"."11_fct_posts"
          (id, org_id, workspace_id, content_text, media_urls, first_comment,
           scheduled_at, status_id, author_user_id, created_by, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10)
        """,
        id, org_id, workspace_id, content_text,
        media_urls,  # asyncpg handles Python lists as JSONB natively
        first_comment, scheduled_at, status_id, author_user_id, created_by,
    )
    post = await get_post(conn, post_id=id)
    return post  # type: ignore[return-value]


async def add_post_account_link(
    conn: Any, *, id: str, post_id: str, account_id: str
) -> None:
    await conn.execute(
        """
        INSERT INTO "07_social"."40_lnk_post_accounts" (id, post_id, account_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (post_id, account_id) DO NOTHING
        """,
        id, post_id, account_id,
    )


async def list_posts(
    conn: Any,
    *,
    org_id: str,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    if status:
        rows = await conn.fetch(
            'SELECT * FROM "07_social"."v_posts" WHERE org_id = $1 AND status = $2 '
            'ORDER BY COALESCE(scheduled_at, created_at) LIMIT $3 OFFSET $4',
            org_id, status, limit, offset,
        )
    else:
        rows = await conn.fetch(
            'SELECT * FROM "07_social"."v_posts" WHERE org_id = $1 '
            'ORDER BY COALESCE(scheduled_at, created_at) LIMIT $2 OFFSET $3',
            org_id, limit, offset,
        )
    return [dict(r) for r in rows]


async def count_posts(conn: Any, *, org_id: str, status: str | None = None) -> int:
    if status:
        return await conn.fetchval(
            'SELECT COUNT(*) FROM "07_social"."v_posts" WHERE org_id = $1 AND status = $2',
            org_id, status,
        )
    return await conn.fetchval(
        'SELECT COUNT(*) FROM "07_social"."v_posts" WHERE org_id = $1',
        org_id,
    )


async def get_post(conn: Any, *, post_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT * FROM "07_social"."v_posts" WHERE id = $1',
        post_id,
    )
    return dict(row) if row else None


async def update_post(
    conn: Any, *, post_id: str, updated_by: str, **fields: Any
) -> dict:
    """Update arbitrary fields on 11_fct_posts. Only known columns are allowed."""
    allowed = {
        "content_text", "media_urls", "first_comment", "scheduled_at",
        "status_id", "published_at", "platform_post_ids", "error_message",
        "approved_by_user_id", "approved_at",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        post = await get_post(conn, post_id=post_id)
        return post  # type: ignore[return-value]

    set_parts = []
    values: list[Any] = []
    idx = 1
    for col, val in updates.items():
        # asyncpg handles Python dicts/lists as JSONB natively — no json.dumps needed
        set_parts.append(f"{col} = ${idx}")
        values.append(val)
        idx += 1

    set_parts.append(f"updated_at = CURRENT_TIMESTAMP")
    set_parts.append(f"updated_by = ${idx}")
    values.append(updated_by)
    idx += 1
    values.append(post_id)

    sql = f'UPDATE "07_social"."11_fct_posts" SET {", ".join(set_parts)} WHERE id = ${idx}'
    await conn.execute(sql, *values)
    post = await get_post(conn, post_id=post_id)
    return post  # type: ignore[return-value]


async def soft_delete_post(conn: Any, *, post_id: str, deleted_by: str) -> None:
    await conn.execute(
        """
        UPDATE "07_social"."11_fct_posts"
        SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP,
            updated_by = $2
        WHERE id = $1 AND deleted_at IS NULL
        """,
        post_id, deleted_by,
    )


async def get_due_posts(conn: Any) -> list[dict]:
    """Posts that are scheduled and due to be published now."""
    rows = await conn.fetch(
        """
        SELECT * FROM "07_social"."v_posts"
        WHERE status = 'scheduled'
          AND scheduled_at <= CURRENT_TIMESTAMP
        ORDER BY scheduled_at
        LIMIT 100
        """,
    )
    return [dict(r) for r in rows]


async def update_post_status(
    conn: Any,
    *,
    post_id: str,
    status_id: int,
    platform_post_ids: dict | None = None,
    error_message: str | None = None,
    published_at: Any = None,
) -> None:
    fields: dict[str, Any] = {"status_id": status_id}
    if platform_post_ids is not None:
        fields["platform_post_ids"] = platform_post_ids
    if error_message is not None:
        fields["error_message"] = error_message
    if published_at is not None:
        fields["published_at"] = published_at
    await update_post(conn, post_id=post_id, updated_by="system", **fields)


async def remove_post_account_links(conn: Any, *, post_id: str) -> None:
    """Remove all account links for a post (used when updating account_ids)."""
    await conn.execute(
        'DELETE FROM "07_social"."40_lnk_post_accounts" WHERE post_id = $1',
        post_id,
    )


# ── Delivery / metrics ───────────────────────────────────────────────────────

async def insert_delivery_log(
    conn: Any,
    *,
    id: str,
    org_id: str,
    post_id: str,
    account_id: str,
    platform_id: int,
    outcome: str,
    platform_post_id: str | None = None,
    error_detail: str | None = None,
) -> None:
    await conn.execute(
        """
        INSERT INTO "07_social"."60_evt_post_deliveries"
          (id, org_id, post_id, account_id, platform_id, platform_post_id,
           outcome, error_detail, published_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8,
                CASE WHEN $7 = 'success' THEN CURRENT_TIMESTAMP ELSE NULL END)
        """,
        id, org_id, post_id, account_id, platform_id,
        platform_post_id, outcome, error_detail,
    )


async def insert_metrics(
    conn: Any,
    *,
    id: str,
    org_id: str,
    post_id: str,
    account_id: str,
    platform_id: int,
    platform_post_id: str,
    impressions: int = 0,
    likes: int = 0,
    reposts: int = 0,
    replies: int = 0,
    bookmarks: int = 0,
    clicks: int = 0,
    raw_data: dict | None = None,
) -> None:
    await conn.execute(
        """
        INSERT INTO "07_social"."61_evt_post_metrics"
          (id, org_id, post_id, account_id, platform_id, platform_post_id,
           impressions, likes, reposts, replies, bookmarks, clicks, raw_data)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """,
        id, org_id, post_id, account_id, platform_id, platform_post_id,
        impressions, likes, reposts, replies, bookmarks, clicks,
        raw_data or {},  # asyncpg handles Python dicts as JSONB natively
    )


async def get_post_metrics(conn: Any, *, post_id: str) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT m.id, m.post_id, m.account_id, m.platform_id,
               pl.code AS platform, m.platform_post_id, m.fetched_at,
               m.impressions, m.likes, m.reposts, m.replies,
               m.bookmarks, m.clicks, m.raw_data
        FROM "07_social"."61_evt_post_metrics" m
        JOIN "07_social"."01_dim_platforms" pl ON pl.id = m.platform_id
        WHERE m.post_id = $1
        ORDER BY m.fetched_at DESC
        """,
        post_id,
    )
    return [dict(r) for r in rows]


async def get_accounts_for_post(conn: Any, *, post_id: str) -> list[dict]:
    """Return social account rows linked to a post (with vault_key for publishing)."""
    rows = await conn.fetch(
        """
        SELECT sa.id, sa.org_id, sa.platform_id, sa.vault_key, sa.account_handle,
               pl.code AS platform
        FROM "07_social"."40_lnk_post_accounts" lnk
        JOIN "07_social"."10_fct_social_accounts" sa ON sa.id = lnk.account_id
        JOIN "07_social"."01_dim_platforms" pl ON pl.id = sa.platform_id
        WHERE lnk.post_id = $1 AND sa.deleted_at IS NULL
        """,
        post_id,
    )
    return [dict(r) for r in rows]

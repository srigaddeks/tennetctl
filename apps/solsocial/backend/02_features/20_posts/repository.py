"""Post repository."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.solsocial.backend.01_core.id")

SCHEMA = '"10_solsocial"'


def _naive_utc(ts: Any) -> Any:
    """Convert an aware datetime to a naive UTC datetime for Postgres TIMESTAMP.
    tennetctl convention: always store naive UTC."""
    if ts is None:
        return None
    tzinfo = getattr(ts, "tzinfo", None)
    if tzinfo is not None:
        from datetime import timezone
        return ts.astimezone(timezone.utc).replace(tzinfo=None)
    return ts


async def resolve_status_id(conn: Any, code: str) -> int | None:
    row = await conn.fetchrow(
        f'SELECT id FROM {SCHEMA}."02_dim_post_statuses" WHERE code = $1', code,
    )
    return int(row["id"]) if row else None


async def list_posts(
    conn: Any,
    *,
    workspace_id: str,
    status: str | None,
    channel_id: str | None,
    limit: int,
    offset: int,
) -> list[dict]:
    where = ["workspace_id = $1"]
    params: list[Any] = [workspace_id]
    if status:
        params.append(status)
        where.append(f"status = ${len(params)}")
    if channel_id:
        params.append(channel_id)
        where.append(f"channel_id = ${len(params)}")
    params.append(limit)
    params.append(offset)
    sql = (
        f'SELECT * FROM {SCHEMA}.v_posts WHERE {" AND ".join(where)} '
        f'ORDER BY COALESCE(scheduled_at, created_at) DESC '
        f'LIMIT ${len(params) - 1} OFFSET ${len(params)}'
    )
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def get(conn: Any, *, post_id: str, workspace_id: str) -> dict | None:
    row = await conn.fetchrow(
        f'SELECT * FROM {SCHEMA}.v_posts WHERE id = $1 AND workspace_id = $2',
        post_id, workspace_id,
    )
    return dict(row) if row else None


async def insert(
    conn: Any,
    *,
    org_id: str,
    workspace_id: str,
    channel_id: str,
    status_id: int,
    body: str,
    media: list[dict],
    link: str | None,
    scheduled_at: Any,
    created_by: str,
) -> str:
    post_id = _id.uuid7()
    async with conn.transaction():
        await conn.execute(
            f'INSERT INTO {SCHEMA}."11_fct_posts" '
            '(id, org_id, workspace_id, channel_id, status_id, created_by, updated_by, scheduled_at) '
            'VALUES ($1, $2, $3, $4, $5, $6, $6, $7)',
            post_id, org_id, workspace_id, channel_id, status_id, created_by,
            _naive_utc(scheduled_at),
        )
        await conn.execute(
            f'INSERT INTO {SCHEMA}."21_dtl_post_content" '
            '(post_id, body, media, link) VALUES ($1, $2, $3, $4)',
            post_id, body, media, link,
        )
    return post_id


async def update(
    conn: Any,
    *,
    post_id: str,
    workspace_id: str,
    body: str | None,
    media: list[dict] | None,
    link: str | None,
    status_id: int | None,
    scheduled_at: Any,
    scheduled_at_set: bool,
) -> None:
    async with conn.transaction():
        fct_sets = ["updated_at = CURRENT_TIMESTAMP"]
        fct_params: list[Any] = []
        if status_id is not None:
            fct_params.append(status_id)
            fct_sets.append(f"status_id = ${len(fct_params)}")
        if scheduled_at_set:
            fct_params.append(_naive_utc(scheduled_at))
            fct_sets.append(f"scheduled_at = ${len(fct_params)}")
        fct_params.extend([post_id, workspace_id])
        await conn.execute(
            f'UPDATE {SCHEMA}."11_fct_posts" SET {", ".join(fct_sets)} '
            f'WHERE id = ${len(fct_params) - 1} AND workspace_id = ${len(fct_params)} '
            'AND deleted_at IS NULL',
            *fct_params,
        )
        dtl_sets = []
        dtl_params: list[Any] = []
        if body is not None:
            dtl_params.append(body)
            dtl_sets.append(f"body = ${len(dtl_params)}")
        if media is not None:
            dtl_params.append(media)
            dtl_sets.append(f"media = ${len(dtl_params)}")
        if link is not None:
            dtl_params.append(link)
            dtl_sets.append(f"link = ${len(dtl_params)}")
        if dtl_sets:
            dtl_params.append(post_id)
            await conn.execute(
                f'UPDATE {SCHEMA}."21_dtl_post_content" SET {", ".join(dtl_sets)} '
                f'WHERE post_id = ${len(dtl_params)}',
                *dtl_params,
            )


async def soft_delete(conn: Any, *, post_id: str, workspace_id: str) -> bool:
    result = await conn.execute(
        f'UPDATE {SCHEMA}."11_fct_posts" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $1 AND workspace_id = $2 AND deleted_at IS NULL',
        post_id, workspace_id,
    )
    return result.endswith(" 1")


async def mark_published(
    conn: Any,
    *,
    post_id: str,
    external_post_id: str,
    external_url: str | None,
    status_id_published: int,
    org_id: str,
    actor_id: str,
) -> None:
    async with conn.transaction():
        await conn.execute(
            f'UPDATE {SCHEMA}."11_fct_posts" '
            'SET status_id = $1, published_at = CURRENT_TIMESTAMP, '
            'updated_at = CURRENT_TIMESTAMP WHERE id = $2',
            status_id_published, post_id,
        )
        await conn.execute(
            f'INSERT INTO {SCHEMA}."22_dtl_post_external" '
            '(post_id, external_post_id, external_url) VALUES ($1, $2, $3) '
            'ON CONFLICT (post_id) DO UPDATE SET '
            'external_post_id = EXCLUDED.external_post_id, '
            'external_url = EXCLUDED.external_url, '
            'published_at = CURRENT_TIMESTAMP',
            post_id, external_post_id, external_url,
        )
        await conn.execute(
            f'INSERT INTO {SCHEMA}."60_evt_post_publishes" '
            '(id, org_id, actor_id, post_id, outcome, metadata) '
            'VALUES ($1, $2, $3, $4, $5, $6)',
            _id.uuid7(), org_id, actor_id, post_id, "success",
            {"external_post_id": external_post_id, "external_url": external_url},
        )


async def mark_failed(
    conn: Any, *, post_id: str, status_id_failed: int,
    error_code: str, error_msg: str, org_id: str, actor_id: str,
) -> None:
    async with conn.transaction():
        await conn.execute(
            f'UPDATE {SCHEMA}."11_fct_posts" '
            'SET status_id = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
            status_id_failed, post_id,
        )
        await conn.execute(
            f'INSERT INTO {SCHEMA}."60_evt_post_publishes" '
            '(id, org_id, actor_id, post_id, outcome, metadata) '
            'VALUES ($1, $2, $3, $4, $5, $6)',
            _id.uuid7(), org_id, actor_id, post_id, "failure",
            {"error_code": error_code, "error_msg": error_msg},
        )

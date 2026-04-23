"""Idea repository."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.solsocial.backend.01_core.id")

SCHEMA = '"10_solsocial"'


async def list_ideas(conn: Any, *, workspace_id: str, limit: int, offset: int) -> list[dict]:
    rows = await conn.fetch(
        f'SELECT * FROM {SCHEMA}.v_ideas WHERE workspace_id = $1 '
        'ORDER BY created_at DESC LIMIT $2 OFFSET $3',
        workspace_id, limit, offset,
    )
    return [dict(r) for r in rows]


async def get(conn: Any, *, idea_id: str, workspace_id: str) -> dict | None:
    row = await conn.fetchrow(
        f'SELECT * FROM {SCHEMA}.v_ideas WHERE id = $1 AND workspace_id = $2',
        idea_id, workspace_id,
    )
    return dict(row) if row else None


async def insert(
    conn: Any, *, org_id: str, workspace_id: str, created_by: str,
    title: str, notes: str | None, tags: list[str],
) -> str:
    idea_id = _id.uuid7()
    async with conn.transaction():
        await conn.execute(
            f'INSERT INTO {SCHEMA}."13_fct_ideas" '
            '(id, org_id, workspace_id, created_by, updated_by) VALUES ($1, $2, $3, $4, $4)',
            idea_id, org_id, workspace_id, created_by,
        )
        await conn.execute(
            f'INSERT INTO {SCHEMA}."24_dtl_idea_content" '
            '(idea_id, title, notes, tags) VALUES ($1, $2, $3, $4)',
            idea_id, title, notes, tags,
        )
    return idea_id


async def update(
    conn: Any, *, idea_id: str, workspace_id: str,
    title: str | None, notes: str | None, tags: list[str] | None,
) -> None:
    sets = []
    params: list[Any] = []
    if title is not None:
        params.append(title)
        sets.append(f"title = ${len(params)}")
    if notes is not None:
        params.append(notes)
        sets.append(f"notes = ${len(params)}")
    if tags is not None:
        params.append(tags)
        sets.append(f"tags = ${len(params)}")
    if sets:
        params.append(idea_id)
        await conn.execute(
            f'UPDATE {SCHEMA}."24_dtl_idea_content" SET {", ".join(sets)} '
            f'WHERE idea_id = ${len(params)}',
            *params,
        )
    await conn.execute(
        f'UPDATE {SCHEMA}."13_fct_ideas" SET updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $1 AND workspace_id = $2',
        idea_id, workspace_id,
    )


async def soft_delete(conn: Any, *, idea_id: str, workspace_id: str) -> bool:
    result = await conn.execute(
        f'UPDATE {SCHEMA}."13_fct_ideas" SET deleted_at = CURRENT_TIMESTAMP, '
        'updated_at = CURRENT_TIMESTAMP WHERE id = $1 AND workspace_id = $2 AND deleted_at IS NULL',
        idea_id, workspace_id,
    )
    return result.endswith(" 1")

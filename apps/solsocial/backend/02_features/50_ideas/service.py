"""Idea service."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.solsocial.backend.02_features.50_ideas.repository")
_errors = import_module("apps.solsocial.backend.01_core.errors")


async def list_ideas(conn: Any, *, workspace_id: str, limit: int, offset: int) -> list[dict]:
    return await _repo.list_ideas(
        conn, workspace_id=workspace_id, limit=limit, offset=offset,
    )


async def get_idea(conn: Any, *, idea_id: str, workspace_id: str) -> dict:
    row = await _repo.get(conn, idea_id=idea_id, workspace_id=workspace_id)
    if not row:
        raise _errors.NotFoundError(f"Idea {idea_id} not found.")
    return row


async def create_idea(
    conn: Any, *, org_id: str, workspace_id: str, created_by: str,
    title: str, notes: str | None, tags: list[str],
) -> dict:
    idea_id = await _repo.insert(
        conn, org_id=org_id, workspace_id=workspace_id, created_by=created_by,
        title=title, notes=notes, tags=tags,
    )
    row = await _repo.get(conn, idea_id=idea_id, workspace_id=workspace_id)
    return row or {}


async def patch_idea(
    conn: Any, *, idea_id: str, workspace_id: str,
    title: str | None, notes: str | None, tags: list[str] | None,
) -> dict:
    existing = await _repo.get(conn, idea_id=idea_id, workspace_id=workspace_id)
    if not existing:
        raise _errors.NotFoundError(f"Idea {idea_id} not found.")
    await _repo.update(
        conn, idea_id=idea_id, workspace_id=workspace_id,
        title=title, notes=notes, tags=tags,
    )
    updated = await _repo.get(conn, idea_id=idea_id, workspace_id=workspace_id)
    return updated or existing


async def delete_idea(conn: Any, *, idea_id: str, workspace_id: str) -> None:
    ok = await _repo.soft_delete(conn, idea_id=idea_id, workspace_id=workspace_id)
    if not ok:
        raise _errors.NotFoundError(f"Idea {idea_id} not found.")

"""
audit.saved_views — service layer.

Thin wrappers: repo call + (future) business logic.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo: Any = import_module(
    "backend.02_features.04_audit.sub_features.02_saved_views.repository"
)


async def list_views(conn: Any, *, org_id: str) -> list[dict]:
    return await _repo.list_saved_views(conn, org_id=org_id)


async def create_view(
    conn: Any,
    *,
    org_id: str,
    user_id: str | None,
    name: str,
    filter_json: dict,
    bucket: str,
) -> dict:
    return await _repo.create_saved_view(
        conn,
        org_id=org_id,
        user_id=user_id,
        name=name,
        filter_json=filter_json,
        bucket=bucket,
    )


async def delete_view(conn: Any, *, view_id: str, org_id: str) -> bool:
    return await _repo.delete_saved_view(conn, view_id=view_id, org_id=org_id)

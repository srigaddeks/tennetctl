"""
audit.saved_views — service layer.

Thin wrappers: repo call + audit emission on every mutation via the
canonical `audit.events.emit` node.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo: Any = import_module(
    "backend.02_features.04_audit.sub_features.02_saved_views.repository"
)
_catalog: Any = import_module("backend.01_catalog")

_AUDIT_NODE_KEY = "audit.events.emit"


async def _emit_audit(
    pool: Any,
    ctx: Any,
    *,
    event_key: str,
    metadata: dict,
    outcome: str = "success",
) -> None:
    """Match the canonical pattern from IAM 01_orgs/service.py."""
    if pool is None or ctx is None:
        return
    await _catalog.run_node(
        pool,
        _AUDIT_NODE_KEY,
        ctx,
        {"event_key": event_key, "outcome": outcome, "metadata": metadata},
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
    pool: Any = None,
    ctx: Any = None,
) -> dict:
    view = await _repo.create_saved_view(
        conn,
        org_id=org_id,
        user_id=user_id,
        name=name,
        filter_json=filter_json,
        bucket=bucket,
    )
    await _emit_audit(
        pool, ctx,
        event_key="audit.saved_views.created",
        metadata={
            "name": name,
            "bucket": bucket,
            "view_id": str(view.get("id") or view.get("view_id") or ""),
        },
    )
    return view


async def delete_view(
    conn: Any,
    *,
    view_id: str,
    org_id: str,
    pool: Any = None,
    ctx: Any = None,
) -> bool:
    deleted = await _repo.delete_saved_view(conn, view_id=view_id, org_id=org_id)
    if deleted:
        await _emit_audit(
            pool, ctx,
            event_key="audit.saved_views.deleted",
            metadata={"view_id": view_id},
        )
    return deleted

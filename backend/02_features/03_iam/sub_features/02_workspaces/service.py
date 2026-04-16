"""
iam.workspaces — service layer.

Business rules: parent-org existence validation (via run_node("iam.orgs.get", ...)
— cross-sub-feature contact stays on the sanctioned path), per-org slug
uniqueness, PATCH diff, audit emission.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import asyncpg

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.02_workspaces.repository"
)

_AUDIT_NODE_KEY = "audit.events.emit"
_ORG_GET_NODE_KEY = "iam.orgs.get"


async def _emit_audit(
    pool: Any,
    ctx: Any,
    *,
    event_key: str,
    metadata: dict,
    outcome: str = "success",
) -> None:
    await _catalog.run_node(
        pool,
        _AUDIT_NODE_KEY,
        ctx,
        {"event_key": event_key, "outcome": outcome, "metadata": metadata},
    )


async def _assert_org_exists(pool: Any, ctx: Any, org_id: str) -> None:
    """
    Validate the parent org exists via run_node("iam.orgs.get", ...).

    Using run_node (not a direct import) keeps workspace -> orgs on the
    sanctioned cross-sub-feature path that the linter enforces. ctx.conn
    propagates to the runner via tx=caller so the read stays in our transaction.
    """
    result = await _catalog.run_node(pool, _ORG_GET_NODE_KEY, ctx, {"id": org_id})
    if result.get("org") is None:
        raise _errors.NotFoundError(f"Org {org_id!r} not found.")


async def create_workspace(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
    slug: str,
    display_name: str,
) -> dict:
    """
    Validate parent org exists, enforce per-org slug uniqueness, insert fct +
    dtl, emit audit. Caller owns the transaction on conn (ctx.conn).
    """
    await _assert_org_exists(pool, ctx, org_id)

    existing = await _repo.get_by_org_slug(conn, org_id, slug)
    if existing is not None:
        raise _errors.ConflictError(
            f"workspace with slug {slug!r} already exists in org {org_id!r}",
        )

    ws_id = _core_id.uuid7()
    attr_row_id = _core_id.uuid7()
    created_by = ctx.user_id or "sys"

    try:
        await _repo.insert_workspace(
            conn,
            id=ws_id,
            org_id=org_id,
            slug=slug,
            created_by=created_by,
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError(
            f"workspace with slug {slug!r} already exists in org {org_id!r}",
        ) from e

    await _repo.set_display_name(
        conn,
        workspace_id=ws_id,
        display_name=display_name,
        attr_row_id=attr_row_id,
    )

    await _emit_audit(
        pool,
        ctx,
        event_key="iam.workspaces.created",
        metadata={"workspace_id": ws_id, "org_id": org_id, "slug": slug},
    )

    created = await _repo.get_by_id(conn, ws_id)
    if created is None:
        raise RuntimeError(
            f"workspace {ws_id} not visible after insert — tx isolation issue?"
        )
    return created


async def get_workspace(
    conn: Any,
    _ctx: Any,
    *,
    workspace_id: str,
) -> dict | None:
    return await _repo.get_by_id(conn, workspace_id)


async def list_workspaces(
    conn: Any,
    _ctx: Any,
    *,
    limit: int = 50,
    offset: int = 0,
    org_id: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    return await _repo.list_workspaces(
        conn,
        limit=limit,
        offset=offset,
        org_id=org_id,
        is_active=is_active,
    )


async def update_workspace(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    workspace_id: str,
    slug: str | None = None,
    display_name: str | None = None,
) -> dict:
    current = await _repo.get_by_id(conn, workspace_id)
    if current is None:
        raise _errors.NotFoundError(f"Workspace {workspace_id!r} not found.")

    changed: dict[str, object] = {}

    if slug is not None and slug != current["slug"]:
        collision = await _repo.get_by_org_slug(conn, current["org_id"], slug)
        if collision is not None and collision["id"] != workspace_id:
            raise _errors.ConflictError(
                f"workspace with slug {slug!r} already exists in org {current['org_id']!r}",
            )
        try:
            ok = await _repo.update_workspace_slug(
                conn,
                id=workspace_id,
                slug=slug,
                updated_by=(ctx.user_id or "sys"),
            )
        except asyncpg.UniqueViolationError as e:
            raise _errors.ConflictError(
                f"workspace with slug {slug!r} already exists in org {current['org_id']!r}",
            ) from e
        if not ok:
            raise _errors.NotFoundError(f"Workspace {workspace_id!r} not found.")
        changed["slug"] = slug

    if display_name is not None and display_name != current.get("display_name"):
        attr_row_id = _core_id.uuid7()
        await _repo.set_display_name(
            conn,
            workspace_id=workspace_id,
            display_name=display_name,
            attr_row_id=attr_row_id,
        )
        await _repo.touch_workspace(
            conn,
            id=workspace_id,
            updated_by=(ctx.user_id or "sys"),
        )
        changed["display_name"] = display_name

    if not changed:
        return current

    await _emit_audit(
        pool,
        ctx,
        event_key="iam.workspaces.updated",
        metadata={
            "workspace_id": workspace_id,
            "org_id": current["org_id"],
            "changed": sorted(changed.keys()),
        },
    )

    updated = await _repo.get_by_id(conn, workspace_id)
    if updated is None:
        raise RuntimeError(
            f"workspace {workspace_id} vanished after update — concurrent delete?"
        )
    return updated


async def delete_workspace(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    workspace_id: str,
) -> None:
    current = await _repo.get_by_id(conn, workspace_id)
    if current is None:
        raise _errors.NotFoundError(f"Workspace {workspace_id!r} not found.")

    ok = await _repo.soft_delete_workspace(
        conn,
        id=workspace_id,
        updated_by=(ctx.user_id or "sys"),
    )
    if not ok:
        raise _errors.NotFoundError(f"Workspace {workspace_id!r} not found.")

    await _emit_audit(
        pool,
        ctx,
        event_key="iam.workspaces.deleted",
        metadata={
            "workspace_id": workspace_id,
            "org_id": current["org_id"],
        },
    )

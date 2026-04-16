"""
iam.memberships — service layer.

Validates parent entities (user, org, workspace) via run_node on the sanctioned
cross-sub-feature path, writes lnk rows, emits audit on grant + revoke.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import asyncpg

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.07_memberships.repository"
)

_AUDIT = "audit.events.emit"
_USERS_GET = "iam.users.get"
_ORGS_GET = "iam.orgs.get"
_WORKSPACES_GET = "iam.workspaces.get"


async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict) -> None:
    await _catalog.run_node(
        pool, _AUDIT, ctx,
        {"event_key": event_key, "outcome": "success", "metadata": metadata},
    )


async def _assert_user(pool: Any, ctx: Any, user_id: str) -> None:
    result = await _catalog.run_node(pool, _USERS_GET, ctx, {"id": user_id})
    if result.get("user") is None:
        raise _errors.NotFoundError(f"User {user_id!r} not found.")


async def _assert_org(pool: Any, ctx: Any, org_id: str) -> None:
    result = await _catalog.run_node(pool, _ORGS_GET, ctx, {"id": org_id})
    if result.get("org") is None:
        raise _errors.NotFoundError(f"Org {org_id!r} not found.")


async def _fetch_workspace(pool: Any, ctx: Any, workspace_id: str) -> dict:
    result = await _catalog.run_node(pool, _WORKSPACES_GET, ctx, {"id": workspace_id})
    ws = result.get("workspace")
    if ws is None:
        raise _errors.NotFoundError(f"Workspace {workspace_id!r} not found.")
    return ws


# ── Org memberships ─────────────────────────────────────────────────

async def assign_org(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    user_id: str,
    org_id: str,
) -> dict:
    await _assert_user(pool, ctx, user_id)
    await _assert_org(pool, ctx, org_id)

    if await _repo.get_org_membership_by_pair(conn, user_id, org_id) is not None:
        raise _errors.ConflictError(
            f"user {user_id!r} is already a member of org {org_id!r}",
        )

    membership_id = _core_id.uuid7()
    try:
        await _repo.insert_org_membership(
            conn,
            id=membership_id,
            user_id=user_id,
            org_id=org_id,
            created_by=(ctx.user_id or "sys"),
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError(
            f"user {user_id!r} is already a member of org {org_id!r}",
        ) from e

    await _emit(
        pool, ctx,
        event_key="iam.memberships.org.assigned",
        metadata={"membership_id": membership_id, "user_id": user_id, "org_id": org_id},
    )
    created = await _repo.get_org_membership_by_id(conn, membership_id)
    if created is None:
        raise RuntimeError(f"org membership {membership_id} not visible after insert")
    return created


async def revoke_org(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    membership_id: str,
) -> None:
    existing = await _repo.get_org_membership_by_id(conn, membership_id)
    if existing is None:
        raise _errors.NotFoundError(f"Org membership {membership_id!r} not found.")

    ok = await _repo.delete_org_membership(conn, membership_id)
    if not ok:
        raise _errors.NotFoundError(f"Org membership {membership_id!r} not found.")

    await _emit(
        pool, ctx,
        event_key="iam.memberships.org.revoked",
        metadata={
            "membership_id": membership_id,
            "user_id": existing["user_id"],
            "org_id": existing["org_id"],
        },
    )


async def list_org(
    conn: Any,
    _ctx: Any,
    *,
    limit: int = 50,
    offset: int = 0,
    user_id: str | None = None,
    org_id: str | None = None,
) -> tuple[list[dict], int]:
    return await _repo.list_org_memberships(
        conn, limit=limit, offset=offset, user_id=user_id, org_id=org_id,
    )


async def get_org(conn: Any, _ctx: Any, *, membership_id: str) -> dict | None:
    return await _repo.get_org_membership_by_id(conn, membership_id)


# ── Workspace memberships ───────────────────────────────────────────

async def assign_workspace(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    user_id: str,
    workspace_id: str,
) -> dict:
    await _assert_user(pool, ctx, user_id)
    workspace = await _fetch_workspace(pool, ctx, workspace_id)
    org_id = workspace["org_id"]

    if await _repo.get_workspace_membership_by_pair(conn, user_id, workspace_id) is not None:
        raise _errors.ConflictError(
            f"user {user_id!r} is already a member of workspace {workspace_id!r}",
        )

    membership_id = _core_id.uuid7()
    try:
        await _repo.insert_workspace_membership(
            conn,
            id=membership_id,
            user_id=user_id,
            workspace_id=workspace_id,
            org_id=org_id,
            created_by=(ctx.user_id or "sys"),
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError(
            f"user {user_id!r} is already a member of workspace {workspace_id!r}",
        ) from e

    await _emit(
        pool, ctx,
        event_key="iam.memberships.workspace.assigned",
        metadata={
            "membership_id": membership_id,
            "user_id": user_id,
            "workspace_id": workspace_id,
            "org_id": org_id,
        },
    )
    created = await _repo.get_workspace_membership_by_id(conn, membership_id)
    if created is None:
        raise RuntimeError(f"workspace membership {membership_id} not visible after insert")
    return created


async def revoke_workspace(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    membership_id: str,
) -> None:
    existing = await _repo.get_workspace_membership_by_id(conn, membership_id)
    if existing is None:
        raise _errors.NotFoundError(
            f"Workspace membership {membership_id!r} not found.",
        )

    ok = await _repo.delete_workspace_membership(conn, membership_id)
    if not ok:
        raise _errors.NotFoundError(
            f"Workspace membership {membership_id!r} not found.",
        )

    await _emit(
        pool, ctx,
        event_key="iam.memberships.workspace.revoked",
        metadata={
            "membership_id": membership_id,
            "user_id": existing["user_id"],
            "workspace_id": existing["workspace_id"],
            "org_id": existing["org_id"],
        },
    )


async def list_workspace(
    conn: Any,
    _ctx: Any,
    *,
    limit: int = 50,
    offset: int = 0,
    user_id: str | None = None,
    workspace_id: str | None = None,
    org_id: str | None = None,
) -> tuple[list[dict], int]:
    return await _repo.list_workspace_memberships(
        conn, limit=limit, offset=offset,
        user_id=user_id, workspace_id=workspace_id, org_id=org_id,
    )


async def get_workspace(conn: Any, _ctx: Any, *, membership_id: str) -> dict | None:
    return await _repo.get_workspace_membership_by_id(conn, membership_id)

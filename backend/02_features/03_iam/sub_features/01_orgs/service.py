"""
iam.orgs — service layer.

Business rules: slug uniqueness check, patch-diff fetch, audit emission.
Service never acquires conns — the caller (route or node) is the tx boundary and
passes (pool, conn, ctx). The pool is required because audit emission goes through
`run_node("audit.events.emit", ...)`, whose lookup phase acquires a probe conn from
the pool; the audit row itself writes through ctx.conn (tx=caller).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import asyncpg

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.01_orgs.repository"
)

_AUDIT_NODE_KEY = "audit.events.emit"


async def _emit_audit(
    pool: Any,
    ctx: Any,
    *,
    event_key: str,
    metadata: dict,
    outcome: str = "success",
) -> None:
    """Dispatch audit.events.emit; runner reuses ctx.conn for atomicity."""
    await _catalog.run_node(
        pool,
        _AUDIT_NODE_KEY,
        ctx,
        {"event_key": event_key, "outcome": outcome, "metadata": metadata},
    )


async def create_org(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    slug: str,
    display_name: str,
) -> dict:
    """
    Create a new org + display_name attr, emit audit.

    Raises ConflictError if slug already exists. Caller owns the transaction on `conn`.
    """
    existing = await _repo.get_by_slug(conn, slug)
    if existing is not None:
        raise _errors.ConflictError(
            f"org with slug {slug!r} already exists",
        )

    org_id = _core_id.uuid7()
    attr_row_id = _core_id.uuid7()
    created_by = ctx.user_id or "sys"

    try:
        await _repo.insert_org(
            conn,
            id=org_id,
            slug=slug,
            created_by=created_by,
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError(
            f"org with slug {slug!r} already exists",
        ) from e

    await _repo.set_display_name(
        conn,
        org_id=org_id,
        display_name=display_name,
        attr_row_id=attr_row_id,
    )

    await _emit_audit(
        pool,
        ctx,
        event_key="iam.orgs.created",
        metadata={"org_id": org_id, "slug": slug},
    )

    created = await _repo.get_by_id(conn, org_id)
    if created is None:
        raise RuntimeError(
            f"org {org_id} not visible after insert — tx isolation issue?"
        )
    return created


async def get_org(
    conn: Any,
    _ctx: Any,
    *,
    org_id: str,
) -> dict | None:
    """Read-only — no audit."""
    return await _repo.get_by_id(conn, org_id)


async def list_orgs(
    conn: Any,
    _ctx: Any,
    *,
    limit: int = 50,
    offset: int = 0,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    """Read-only — no audit."""
    return await _repo.list_orgs(
        conn,
        limit=limit,
        offset=offset,
        is_active=is_active,
    )


async def update_org(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
    slug: str | None = None,
    display_name: str | None = None,
) -> dict:
    """
    PATCH — only provided fields change. Raises NotFoundError if missing / deleted.
    Emits audit only when something actually changed.
    """
    current = await _repo.get_by_id(conn, org_id)
    if current is None:
        raise _errors.NotFoundError(f"Org {org_id!r} not found.")

    changed: dict[str, object] = {}

    if slug is not None and slug != current["slug"]:
        collision = await _repo.get_by_slug(conn, slug)
        if collision is not None and collision["id"] != org_id:
            raise _errors.ConflictError(
                f"org with slug {slug!r} already exists",
            )
        try:
            ok = await _repo.update_org_slug(
                conn,
                id=org_id,
                slug=slug,
                updated_by=(ctx.user_id or "sys"),
            )
        except asyncpg.UniqueViolationError as e:
            raise _errors.ConflictError(
                f"org with slug {slug!r} already exists",
            ) from e
        if not ok:
            raise _errors.NotFoundError(f"Org {org_id!r} not found.")
        changed["slug"] = slug

    if display_name is not None and display_name != current.get("display_name"):
        attr_row_id = _core_id.uuid7()
        await _repo.set_display_name(
            conn,
            org_id=org_id,
            display_name=display_name,
            attr_row_id=attr_row_id,
        )
        await _repo.touch_org(
            conn,
            id=org_id,
            updated_by=(ctx.user_id or "sys"),
        )
        changed["display_name"] = display_name

    if not changed:
        return current

    await _emit_audit(
        pool,
        ctx,
        event_key="iam.orgs.updated",
        metadata={"org_id": org_id, "changed": sorted(changed.keys())},
    )

    updated = await _repo.get_by_id(conn, org_id)
    if updated is None:
        raise RuntimeError(
            f"org {org_id} vanished after update — concurrent delete?"
        )
    return updated


async def delete_org(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    org_id: str,
) -> None:
    """Soft delete + audit. Raises NotFoundError if missing / already deleted."""
    ok = await _repo.soft_delete_org(
        conn,
        id=org_id,
        updated_by=(ctx.user_id or "sys"),
    )
    if not ok:
        raise _errors.NotFoundError(f"Org {org_id!r} not found.")

    await _emit_audit(
        pool,
        ctx,
        event_key="iam.orgs.deleted",
        metadata={"org_id": org_id},
    )

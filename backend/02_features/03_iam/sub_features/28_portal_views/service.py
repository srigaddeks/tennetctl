"""iam.portal_views — service layer.

Resolves which portal views a user sees (via role chain) and lets admins
manage role→view grants.

Audit events emitted:
  iam.portal_views.attached   — view attached to role
  iam.portal_views.detached   — view detached from role
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.28_portal_views.repository"
)

_AUDIT_NODE = "audit.events.emit"


# ── helpers ────────────────────────────────────────────────────────────────────

async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict) -> None:
    """Fire-and-forget audit emission — never raises."""
    try:
        await _catalog.run_node(
            pool,
            _AUDIT_NODE,
            ctx,
            {"event_key": event_key, "outcome": "success", "metadata": metadata},
        )
    except Exception:  # noqa: BLE001
        pass


def _build_ctx(pool: Any, user_id: str | None, session_id: str | None, org_id: str | None) -> Any:
    _catalog_ctx: Any = import_module("backend.01_catalog.context")
    return _catalog_ctx.NodeContext(
        user_id=user_id,
        session_id=session_id,
        org_id=org_id,
        workspace_id=None,
        application_id=None,
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(),
        audit_category="setup",
        pool=pool,
        extras={"pool": pool},
    )


# ── Public reads ───────────────────────────────────────────────────────────────

async def list_all_views(conn: Any) -> list[dict]:
    """Return all non-deprecated portal views (global catalog, no auth required)."""
    return await _repo.list_all_views(conn)


async def list_role_views(conn: Any, role_id: str) -> list[dict]:
    """Return views granted to a specific role, with joined dim data."""
    return await _repo.list_role_views(conn, role_id)


async def resolve_my_views(conn: Any, *, user_id: str, org_id: str) -> list[dict]:
    """Resolve the current user's portal views via role chain.

    If the user has no role-view grants, returns ALL non-deprecated views as a
    first-run convenience (platform works before any grants are configured).
    """
    views = await _repo.resolve_my_views(conn, user_id, org_id)
    if not views:
        # First-run fallback: no grants yet → show everything
        views = await _repo.list_all_views(conn)
    return views


# ── Mutations ──────────────────────────────────────────────────────────────────

async def attach_view(
    pool: Any,
    conn: Any,
    *,
    role_id: str,
    view_id: int,
    org_id: str,
    actor_id: str,
    session_id: str | None,
) -> dict:
    """Grant a portal view to a role.

    Idempotent — attaching an already-granted view is a no-op that returns
    the existing row.
    """
    # Verify the view exists
    view = await _repo.get_view_by_id(conn, view_id)
    if view is None:
        raise _errors.AppError("NOT_FOUND", f"Portal view {view_id} not found.", 404)

    row = await _repo.attach_view(
        conn,
        id=_core_id.uuid7(),
        role_id=role_id,
        view_id=view_id,
        org_id=org_id,
        created_by=actor_id,
    )
    ctx = _build_ctx(pool, actor_id, session_id, org_id)
    await _emit(pool, ctx, event_key="iam.portal_views.attached", metadata={
        "role_id": role_id,
        "view_id": view_id,
        "view_code": view["code"],
        "org_id": org_id,
    })
    return row


async def detach_view(
    pool: Any,
    conn: Any,
    *,
    role_id: str,
    view_id: int,
    org_id: str,
    actor_id: str,
    session_id: str | None,
) -> None:
    """Revoke a portal view from a role. Raises NOT_FOUND if the grant doesn't exist."""
    # Verify the view exists for a useful error message
    view = await _repo.get_view_by_id(conn, view_id)
    if view is None:
        raise _errors.AppError("NOT_FOUND", f"Portal view {view_id} not found.", 404)

    deleted = await _repo.detach_view(conn, role_id=role_id, view_id=view_id)
    if not deleted:
        raise _errors.AppError(
            "NOT_FOUND",
            f"View {view_id} is not granted to role {role_id!r}.",
            404,
        )
    ctx = _build_ctx(pool, actor_id, session_id, org_id)
    await _emit(pool, ctx, event_key="iam.portal_views.detached", metadata={
        "role_id": role_id,
        "view_id": view_id,
        "view_code": view["code"],
        "org_id": org_id,
    })

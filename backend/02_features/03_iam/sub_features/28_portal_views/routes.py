"""iam.portal_views — FastAPI routes.

Endpoints:
  GET    /v1/iam/portal-views                    list all portal views (global dim)
  GET    /v1/iam/roles/{role_id}/views            list views granted to a role
  POST   /v1/iam/roles/{role_id}/views            attach a view to a role
  DELETE /v1/iam/roles/{role_id}/views/{view_id}  detach a view from a role
  GET    /v1/iam/my-views                         resolve current user's views
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_resp: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.28_portal_views.service"
)
_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.28_portal_views.schemas"
)

AttachViewBody = _schemas.AttachViewBody
PortalViewOut = _schemas.PortalViewOut
MyViewItem = _schemas.MyViewItem

router = APIRouter(prefix="/v1/iam", tags=["iam.portal_views"])


# ── helpers ────────────────────────────────────────────────────────────────────

def _require_user(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    return user_id


def _require_org(request: Request) -> str:
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise _errors.AppError("BAD_REQUEST", "Org context required.", 400)
    return org_id


def _session_id(request: Request) -> str | None:
    return getattr(request.state, "session_id", None)


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/portal-views")
async def list_views_route(request: Request) -> Any:
    """List all non-deprecated portal views — global catalog, no auth required."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        views = await _service.list_all_views(conn)
    return _resp.success_response(
        [PortalViewOut(**v).model_dump(mode="json") for v in views]
    )


@router.get("/roles/{role_id}/views")
async def list_role_views_route(role_id: str, request: Request) -> Any:
    """List views currently granted to a role."""
    _require_user(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_role_views(conn, role_id)
    return _resp.success_response(
        [_schemas.RoleViewAssignment(**r).model_dump(mode="json") for r in rows]
    )


@router.post("/roles/{role_id}/views", status_code=201)
async def attach_view_route(role_id: str, body: AttachViewBody, request: Request) -> Any:
    """Grant a portal view to a role."""
    actor_id = _require_user(request)
    org_id = _require_org(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.attach_view(
            pool,
            conn,
            role_id=role_id,
            view_id=body.view_id,
            org_id=org_id,
            actor_id=actor_id,
            session_id=_session_id(request),
        )
    return _resp.success_response(
        _schemas.RoleViewAssignment(**row).model_dump(mode="json"),
        status_code=201,
    )


@router.delete("/roles/{role_id}/views/{view_id}", status_code=204)
async def detach_view_route(role_id: str, view_id: int, request: Request) -> None:
    """Revoke a portal view from a role."""
    actor_id = _require_user(request)
    org_id = _require_org(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        await _service.detach_view(
            pool,
            conn,
            role_id=role_id,
            view_id=view_id,
            org_id=org_id,
            actor_id=actor_id,
            session_id=_session_id(request),
        )
    return None


@router.get("/my-views")
async def my_views_route(request: Request) -> Any:
    """Return the current user's granted portal views, resolved via role chain.

    Falls back to ALL views when no role-view grants exist (first-run convenience).
    """
    user_id = _require_user(request)
    org_id = _require_org(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        views = await _service.resolve_my_views(conn, user_id=user_id, org_id=org_id)
    return _resp.success_response(
        [MyViewItem(**v).model_dump(mode="json") for v in views]
    )

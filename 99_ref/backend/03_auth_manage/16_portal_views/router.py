from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request, status

from .dependencies import get_portal_view_service
from .schemas import (
    AddViewRouteRequest,
    AssignViewToRoleRequest,
    CreatePortalViewRequest,
    PortalViewDetailResponse,
    PortalViewListResponse,
    RoleViewListResponse,
    UpdatePortalViewRequest,
    UserViewsResponse,
    ViewRouteResponse,
)
from .service import PortalViewService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/am/views", tags=["portal-views"])


# ── Public (JWT-only, no permission required) ────────────────────────────────

@router.get("/my-views", response_model=UserViewsResponse)
async def get_my_views(
    service: Annotated[PortalViewService, Depends(get_portal_view_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(default=None),
) -> UserViewsResponse:
    """Return all portal views available to the current user, scoped to the given org."""
    return await service.resolve_user_views(user_id=claims.subject, org_id=org_id)


# ── Admin endpoints (requires access_governance_console.view) ────────────────

@router.get("", response_model=PortalViewListResponse)
async def list_views(
    service: Annotated[PortalViewService, Depends(get_portal_view_service)],
    claims=Depends(get_current_access_claims),
) -> PortalViewListResponse:
    """List all portal views with their routes."""
    return await service.list_views(actor_id=claims.subject)


@router.get("/role-assignments", response_model=RoleViewListResponse)
async def list_all_role_view_assignments(
    service: Annotated[PortalViewService, Depends(get_portal_view_service)],
    claims=Depends(get_current_access_claims),
) -> RoleViewListResponse:
    """List all role → view assignments."""
    return await service.list_all_role_view_assignments(actor_id=claims.subject)


@router.get("/roles/{role_id}", response_model=RoleViewListResponse)
async def list_role_views(
    role_id: str,
    service: Annotated[PortalViewService, Depends(get_portal_view_service)],
    claims=Depends(get_current_access_claims),
) -> RoleViewListResponse:
    """List views assigned to a specific role."""
    return await service.list_role_views(role_id, actor_id=claims.subject)


# ── Admin mutations (requires group_access_assignment.assign) ────────────────

@router.post("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def assign_view_to_role(
    role_id: str,
    payload: AssignViewToRoleRequest,
    request: Request,
    service: Annotated[PortalViewService, Depends(get_portal_view_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Assign a portal view to a role."""
    await service.assign_view_to_role(
        role_id,
        payload,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/roles/{role_id}/{view_code}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_view_from_role(
    role_id: str,
    view_code: str,
    request: Request,
    service: Annotated[PortalViewService, Depends(get_portal_view_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Revoke a portal view from a role."""
    await service.revoke_view_from_role(
        role_id,
        view_code,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


# ── View CRUD ────────────────────────────────────────────────────────────────

@router.post("", response_model=PortalViewDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_view(
    payload: CreatePortalViewRequest,
    request: Request,
    service: Annotated[PortalViewService, Depends(get_portal_view_service)],
    claims=Depends(get_current_access_claims),
) -> PortalViewDetailResponse:
    """Create a new portal view."""
    return await service.create_view(
        payload, actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/{code}", response_model=PortalViewDetailResponse)
async def update_view(
    code: str,
    payload: UpdatePortalViewRequest,
    request: Request,
    service: Annotated[PortalViewService, Depends(get_portal_view_service)],
    claims=Depends(get_current_access_claims),
) -> PortalViewDetailResponse:
    """Update an existing portal view."""
    return await service.update_view(
        code, payload, actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_view(
    code: str,
    request: Request,
    service: Annotated[PortalViewService, Depends(get_portal_view_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Delete a portal view."""
    await service.delete_view(
        code, actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.put("/{code}/routes", response_model=ViewRouteResponse, status_code=status.HTTP_200_OK)
async def add_route(
    code: str,
    payload: AddViewRouteRequest,
    service: Annotated[PortalViewService, Depends(get_portal_view_service)],
    claims=Depends(get_current_access_claims),
) -> ViewRouteResponse:
    """Add or update a route in a portal view (upsert)."""
    return await service.add_route(code, payload, actor_id=claims.subject)


@router.delete("/{code}/routes/{route_prefix:path}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_route(
    code: str,
    route_prefix: str,
    service: Annotated[PortalViewService, Depends(get_portal_view_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Remove a route from a portal view."""
    # route_prefix from path won't have leading slash — restore it
    prefix = route_prefix if route_prefix.startswith("/") else f"/{route_prefix}"
    await service.remove_route(code, prefix, actor_id=claims.subject)

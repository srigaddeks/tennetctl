from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request, status

from .dependencies import get_role_service
from .schemas import (
    AssignPermissionRequest,
    CreateRoleRequest,
    RoleGroupListResponse,
    RoleListResponse,
    RoleResponse,
    UpdateRoleRequest,
)
from .service import RoleService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/am/roles", tags=["access-management"])


@router.get("", response_model=RoleListResponse)
async def list_roles(
    service: Annotated[RoleService, Depends(get_role_service)],
    claims=Depends(get_current_access_claims),
    scope_org_id: str | None = Query(default=None),
) -> RoleListResponse:
    return await service.list_roles(actor_id=claims.subject, scope_org_id=scope_org_id)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=RoleResponse)
async def create_role(
    payload: CreateRoleRequest,
    request: Request,
    service: Annotated[RoleService, Depends(get_role_service)],
    claims=Depends(get_current_access_claims),
) -> RoleResponse:
    return await service.create_role(
        payload,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: str,
    payload: UpdateRoleRequest,
    request: Request,
    service: Annotated[RoleService, Depends(get_role_service)],
    claims=Depends(get_current_access_claims),
) -> RoleResponse:
    return await service.update_role(
        role_id, payload,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/{role_id}/groups", response_model=RoleGroupListResponse)
async def list_groups_using_role(
    role_id: str,
    service: Annotated[RoleService, Depends(get_role_service)],
    claims=Depends(get_current_access_claims),
    scope_org_id: str | None = Query(default=None),
) -> RoleGroupListResponse:
    return await service.list_groups_using_role(
        role_id,
        actor_id=claims.subject,
        scope_org_id=scope_org_id,
    )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: str,
    request: Request,
    service: Annotated[RoleService, Depends(get_role_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_role(
        role_id,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/{role_id}/permissions", status_code=status.HTTP_201_CREATED, response_model=RoleResponse)
async def assign_permission(
    role_id: str,
    payload: AssignPermissionRequest,
    request: Request,
    service: Annotated[RoleService, Depends(get_role_service)],
    claims=Depends(get_current_access_claims),
) -> RoleResponse:
    return await service.assign_permission(
        role_id, payload,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_permission(
    role_id: str,
    permission_id: str,
    request: Request,
    service: Annotated[RoleService, Depends(get_role_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.revoke_permission(
        role_id, permission_id,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )

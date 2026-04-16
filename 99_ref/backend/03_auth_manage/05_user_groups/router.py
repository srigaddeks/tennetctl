from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request, status

from .dependencies import get_user_group_service
from .schemas import (
    AddMemberRequest,
    AssignGroupRoleRequest,
    CreateGroupRequest,
    GroupChildListResponse,
    GroupListResponse,
    GroupMemberListResponse,
    GroupResponse,
    SetParentGroupRequest,
    UpdateGroupRequest,
)
from .service import UserGroupService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/am/groups", tags=["access-management"])


@router.get("", response_model=GroupListResponse)
async def list_groups(
    service: Annotated[UserGroupService, Depends(get_user_group_service)],
    claims=Depends(get_current_access_claims),
    scope_org_id: str | None = Query(default=None),
) -> GroupListResponse:
    return await service.list_groups(actor_id=claims.subject, scope_org_id=scope_org_id)


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    service: Annotated[UserGroupService, Depends(get_user_group_service)],
    claims=Depends(get_current_access_claims),
) -> GroupResponse:
    return await service.get_group(group_id, actor_id=claims.subject)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=GroupResponse)
async def create_group(
    payload: CreateGroupRequest,
    request: Request,
    service: Annotated[UserGroupService, Depends(get_user_group_service)],
    claims=Depends(get_current_access_claims),
) -> GroupResponse:
    return await service.create_group(
        payload,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    payload: UpdateGroupRequest,
    request: Request,
    service: Annotated[UserGroupService, Depends(get_user_group_service)],
    claims=Depends(get_current_access_claims),
) -> GroupResponse:
    return await service.update_group(
        group_id, payload,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.put("/{group_id}/parent", response_model=GroupResponse)
async def set_parent(
    group_id: str,
    payload: SetParentGroupRequest,
    request: Request,
    service: Annotated[UserGroupService, Depends(get_user_group_service)],
    claims=Depends(get_current_access_claims),
) -> GroupResponse:
    return await service.set_parent(
        group_id, payload,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    request: Request,
    service: Annotated[UserGroupService, Depends(get_user_group_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_group(
        group_id,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/{group_id}/members", response_model=GroupMemberListResponse)
async def list_members(
    group_id: str,
    service: Annotated[UserGroupService, Depends(get_user_group_service)],
    claims=Depends(get_current_access_claims),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> GroupMemberListResponse:
    return await service.list_group_members(group_id, actor_id=claims.subject, limit=limit, offset=offset)


@router.get("/{group_id}/children", response_model=GroupChildListResponse)
async def list_children(
    group_id: str,
    service: Annotated[UserGroupService, Depends(get_user_group_service)],
    claims=Depends(get_current_access_claims),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> GroupChildListResponse:
    return await service.list_group_children(group_id, actor_id=claims.subject, limit=limit, offset=offset)


@router.post("/{group_id}/members", status_code=status.HTTP_201_CREATED, response_model=GroupResponse)
async def add_member(
    group_id: str,
    payload: AddMemberRequest,
    request: Request,
    service: Annotated[UserGroupService, Depends(get_user_group_service)],
    claims=Depends(get_current_access_claims),
) -> GroupResponse:
    return await service.add_member(
        group_id, payload,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: str,
    user_id: str,
    request: Request,
    service: Annotated[UserGroupService, Depends(get_user_group_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.remove_member(
        group_id, user_id,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/{group_id}/roles", status_code=status.HTTP_201_CREATED, response_model=GroupResponse)
async def assign_role(
    group_id: str,
    payload: AssignGroupRoleRequest,
    request: Request,
    service: Annotated[UserGroupService, Depends(get_user_group_service)],
    claims=Depends(get_current_access_claims),
) -> GroupResponse:
    return await service.assign_role(
        group_id, payload,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/{group_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_role(
    group_id: str,
    role_id: str,
    request: Request,
    service: Annotated[UserGroupService, Depends(get_user_group_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.revoke_role(
        group_id, role_id,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )

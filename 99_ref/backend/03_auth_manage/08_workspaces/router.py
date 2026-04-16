from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, status

from .dependencies import get_workspace_service
from .schemas import (
    AddWorkspaceMemberRequest,
    CreateWorkspaceRequest,
    UpdateWorkspaceMemberRequest,
    UpdateWorkspaceRequest,
    WorkspaceListResponse,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceTypeResponse,
)
from .service import WorkspaceService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/am", tags=["workspaces"])


@router.get("/workspace-types", response_model=list[WorkspaceTypeResponse])
async def list_workspace_types(
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
) -> list[WorkspaceTypeResponse]:
    return await service.list_workspace_types()


@router.get("/orgs/{org_id}/workspaces", response_model=WorkspaceListResponse)
async def list_workspaces(
    org_id: str,
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    claims=Depends(get_current_access_claims),
) -> WorkspaceListResponse:
    return await service.list_workspaces(user_id=claims.subject, org_id=org_id)


@router.post(
    "/orgs/{org_id}/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace(
    org_id: str,
    body: CreateWorkspaceRequest,
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    claims=Depends(get_current_access_claims),
) -> WorkspaceResponse:
    return await service.create_workspace(
        user_id=claims.subject, org_id=org_id, request=body
    )


@router.patch("/orgs/{org_id}/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    org_id: str,
    workspace_id: str,
    body: UpdateWorkspaceRequest,
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    claims=Depends(get_current_access_claims),
) -> WorkspaceResponse:
    return await service.update_workspace(
        user_id=claims.subject, org_id=org_id, workspace_id=workspace_id, request=body
    )


@router.get(
    "/orgs/{org_id}/workspaces/{workspace_id}/members",
    response_model=list[WorkspaceMemberResponse],
)
async def list_workspace_members(
    org_id: str,
    workspace_id: str,
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    claims=Depends(get_current_access_claims),
) -> list[WorkspaceMemberResponse]:
    return await service.list_members(
        user_id=claims.subject, org_id=org_id, workspace_id=workspace_id
    )


@router.post(
    "/orgs/{org_id}/workspaces/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_workspace_member(
    org_id: str,
    workspace_id: str,
    body: AddWorkspaceMemberRequest,
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    claims=Depends(get_current_access_claims),
) -> WorkspaceMemberResponse:
    return await service.add_member(
        user_id=claims.subject,
        org_id=org_id,
        workspace_id=workspace_id,
        target_user_id=body.user_id,
        role=body.role,
    )


@router.patch(
    "/orgs/{org_id}/workspaces/{workspace_id}/members/{target_user_id}",
    response_model=WorkspaceMemberResponse,
)
async def update_workspace_member(
    org_id: str,
    workspace_id: str,
    target_user_id: str,
    body: UpdateWorkspaceMemberRequest,
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    claims=Depends(get_current_access_claims),
) -> WorkspaceMemberResponse:
    """Assign or remove a GRC role for a workspace member.

    Only valid for GRC workspaces. Set grc_role_code to assign a GRC role,
    or null to remove all GRC role assignments.
    """
    return await service.update_workspace_member(
        user_id=claims.subject,
        org_id=org_id,
        workspace_id=workspace_id,
        target_user_id=target_user_id,
        request=body,
    )


@router.delete(
    "/orgs/{org_id}/workspaces/{workspace_id}/members/{target_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_workspace_member(
    org_id: str,
    workspace_id: str,
    target_user_id: str,
    service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.remove_member(
        user_id=claims.subject,
        org_id=org_id,
        workspace_id=workspace_id,
        target_user_id=target_user_id,
    )

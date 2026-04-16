from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, status

from .dependencies import get_org_service
from .schemas import (
    AddOrgMemberRequest,
    CreateOrgRequest,
    OrgListResponse,
    OrgMemberResponse,
    OrgResponse,
    OrgTypeResponse,
    UpdateOrgMemberRequest,
    UpdateOrgRequest,
)
from .service import OrgService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/am", tags=["orgs"])


@router.get("/org-types", response_model=list[OrgTypeResponse])
async def list_org_types(
    service: Annotated[OrgService, Depends(get_org_service)],
) -> list[OrgTypeResponse]:
    return await service.list_org_types()


@router.get("/orgs", response_model=OrgListResponse)
async def list_orgs(
    service: Annotated[OrgService, Depends(get_org_service)],
    claims=Depends(get_current_access_claims),
) -> OrgListResponse:
    return await service.list_orgs(user_id=claims.subject, tenant_key=claims.tenant_key)


@router.post("/orgs", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_org(
    body: CreateOrgRequest,
    service: Annotated[OrgService, Depends(get_org_service)],
    claims=Depends(get_current_access_claims),
) -> OrgResponse:
    return await service.create_org(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


@router.patch("/orgs/{org_id}", response_model=OrgResponse)
async def update_org(
    org_id: str,
    body: UpdateOrgRequest,
    service: Annotated[OrgService, Depends(get_org_service)],
    claims=Depends(get_current_access_claims),
) -> OrgResponse:
    return await service.update_org(user_id=claims.subject, org_id=org_id, request=body)


@router.get("/orgs/{org_id}/members", response_model=list[OrgMemberResponse])
async def list_org_members(
    org_id: str,
    service: Annotated[OrgService, Depends(get_org_service)],
    claims=Depends(get_current_access_claims),
) -> list[OrgMemberResponse]:
    return await service.list_members(user_id=claims.subject, org_id=org_id)


@router.post(
    "/orgs/{org_id}/members",
    response_model=OrgMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_org_member(
    org_id: str,
    body: AddOrgMemberRequest,
    service: Annotated[OrgService, Depends(get_org_service)],
    claims=Depends(get_current_access_claims),
) -> OrgMemberResponse:
    return await service.add_member(
        user_id=claims.subject,
        org_id=org_id,
        target_user_id=body.user_id,
        role=body.role,
    )


@router.patch("/orgs/{org_id}/members/{target_user_id}", response_model=OrgMemberResponse)
async def update_org_member_role(
    org_id: str,
    target_user_id: str,
    body: UpdateOrgMemberRequest,
    service: Annotated[OrgService, Depends(get_org_service)],
    claims=Depends(get_current_access_claims),
) -> OrgMemberResponse:
    return await service.update_member_role(
        user_id=claims.subject,
        org_id=org_id,
        target_user_id=target_user_id,
        role=body.role,
    )


@router.delete("/orgs/{org_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_org_member(
    org_id: str,
    target_user_id: str,
    service: Annotated[OrgService, Depends(get_org_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.remove_member(
        user_id=claims.subject, org_id=org_id, target_user_id=target_user_id
    )

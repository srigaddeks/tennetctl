from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_policy_service
from .schemas import (
    CreatePolicyRequest,
    PolicyExecutionResponse,
    PolicyListResponse,
    PolicyResponse,
    PolicyTestResponse,
    UpdatePolicyRequest,
)
from .service import PolicyService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/policies", tags=["sandbox-policies"])


@router.get("", response_model=PolicyListResponse)
async def list_policies(
    service: Annotated[PolicyService, Depends(get_policy_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str | None = Query(default=None),
    threat_type_id: str | None = Query(default=None),
    is_enabled: bool | None = Query(default=None),
    sort_by: str = Query(default="policy_code"),
    sort_dir: str = Query(default="ASC"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> PolicyListResponse:
    return await service.list_policies(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        threat_type_id=threat_type_id,
        is_enabled=is_enabled,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: str,
    service: Annotated[PolicyService, Depends(get_policy_service)],
    claims=Depends(get_current_access_claims),
) -> PolicyResponse:
    return await service.get_policy(
        user_id=claims.subject, policy_id=policy_id
    )


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    body: CreatePolicyRequest,
    service: Annotated[PolicyService, Depends(get_policy_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> PolicyResponse:
    return await service.create_policy(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=body,
    )


@router.patch("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    body: UpdatePolicyRequest,
    service: Annotated[PolicyService, Depends(get_policy_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> PolicyResponse:
    return await service.update_policy(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        policy_id=policy_id,
        request=body,
    )


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: str,
    service: Annotated[PolicyService, Depends(get_policy_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    await service.delete_policy(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        policy_id=policy_id,
    )


@router.post("/{policy_id}/enable", response_model=PolicyResponse)
async def enable_policy(
    policy_id: str,
    service: Annotated[PolicyService, Depends(get_policy_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> PolicyResponse:
    return await service.enable_policy(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        policy_id=policy_id,
    )


@router.post("/{policy_id}/disable", response_model=PolicyResponse)
async def disable_policy(
    policy_id: str,
    service: Annotated[PolicyService, Depends(get_policy_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> PolicyResponse:
    return await service.disable_policy(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        policy_id=policy_id,
    )


@router.post("/{policy_id}/test", response_model=PolicyTestResponse)
async def test_policy(
    policy_id: str,
    service: Annotated[PolicyService, Depends(get_policy_service)],
    claims=Depends(get_current_access_claims),
) -> PolicyTestResponse:
    return await service.test_policy(
        user_id=claims.subject, policy_id=policy_id
    )


@router.get("/{policy_id}/versions", response_model=list[PolicyResponse])
async def list_versions(
    policy_id: str,
    service: Annotated[PolicyService, Depends(get_policy_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> list[PolicyResponse]:
    return await service.list_versions(
        user_id=claims.subject,
        org_id=org_id,
        policy_id=policy_id,
    )


@router.get("/{policy_id}/executions", response_model=list[PolicyExecutionResponse])
async def list_executions(
    policy_id: str,
    service: Annotated[PolicyService, Depends(get_policy_service)],
    claims=Depends(get_current_access_claims),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[PolicyExecutionResponse]:
    return await service.list_executions(
        user_id=claims.subject,
        policy_id=policy_id,
        limit=limit,
        offset=offset,
    )

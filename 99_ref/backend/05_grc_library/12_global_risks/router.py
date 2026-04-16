from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_global_risk_service
from .schemas import (
    CreateGlobalRiskRequest,
    DeployGlobalRisksRequest,
    DeployGlobalRisksResponse,
    GlobalRiskListResponse,
    GlobalRiskResponse,
    LinkControlRequest,
    RiskLibraryDeploymentListResponse,
    UpdateGlobalRiskRequest,
)
from .service import GlobalRiskService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/fr", tags=["grc-global-risks"])


@router.get("/global-risks", response_model=GlobalRiskListResponse)
async def list_global_risks(
    service: Annotated[GlobalRiskService, Depends(get_global_risk_service)],
    claims=Depends(get_current_access_claims),
    category: str | None = Query(None),
    search: str | None = Query(None),
    sort_by: str | None = Query(None),
    sort_dir: str | None = Query(None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> GlobalRiskListResponse:
    return await service.list_global_risks(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        category=category,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


@router.get("/global-risks/{global_risk_id}", response_model=GlobalRiskResponse)
async def get_global_risk(
    global_risk_id: str,
    service: Annotated[GlobalRiskService, Depends(get_global_risk_service)],
    claims=Depends(get_current_access_claims),
) -> GlobalRiskResponse:
    return await service.get_global_risk(user_id=claims.subject, global_risk_id=global_risk_id)


@router.post("/global-risks", response_model=GlobalRiskResponse, status_code=status.HTTP_201_CREATED)
async def create_global_risk(
    body: CreateGlobalRiskRequest,
    service: Annotated[GlobalRiskService, Depends(get_global_risk_service)],
    claims=Depends(get_current_access_claims),
) -> GlobalRiskResponse:
    return await service.create_global_risk(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


@router.patch("/global-risks/{global_risk_id}", response_model=GlobalRiskResponse)
async def update_global_risk(
    global_risk_id: str,
    body: UpdateGlobalRiskRequest,
    service: Annotated[GlobalRiskService, Depends(get_global_risk_service)],
    claims=Depends(get_current_access_claims),
) -> GlobalRiskResponse:
    return await service.update_global_risk(
        user_id=claims.subject, global_risk_id=global_risk_id, request=body
    )


@router.delete("/global-risks/{global_risk_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_risk(
    global_risk_id: str,
    service: Annotated[GlobalRiskService, Depends(get_global_risk_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_global_risk(user_id=claims.subject, global_risk_id=global_risk_id)


# ── Control Links ─────────────────────────────────────────────────────────────

@router.post("/global-risks/{global_risk_id}/controls", response_model=GlobalRiskResponse)
async def link_control(
    global_risk_id: str,
    body: LinkControlRequest,
    service: Annotated[GlobalRiskService, Depends(get_global_risk_service)],
    claims=Depends(get_current_access_claims),
) -> GlobalRiskResponse:
    """Link a library control to a global risk."""
    return await service.link_control(
        user_id=claims.subject, global_risk_id=global_risk_id, request=body
    )


@router.delete("/global-risks/{global_risk_id}/controls/{control_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_control(
    global_risk_id: str,
    control_id: str,
    service: Annotated[GlobalRiskService, Depends(get_global_risk_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Remove a control link from a global risk."""
    await service.unlink_control(
        user_id=claims.subject, global_risk_id=global_risk_id, control_id=control_id
    )


# ── Risk Library Deployments ──────────────────────────────────────────────────

@router.get("/risk-library-deployments", response_model=RiskLibraryDeploymentListResponse)
async def list_risk_deployments(
    service: Annotated[GlobalRiskService, Depends(get_global_risk_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str = Query(...),
) -> RiskLibraryDeploymentListResponse:
    """List global risks deployed to a workspace."""
    result = await service.list_risk_deployments(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
    )
    from .schemas import RiskLibraryDeploymentResponse
    return RiskLibraryDeploymentListResponse(
        items=[RiskLibraryDeploymentResponse(**item) for item in result["items"]],
        total=result["total"],
    )


@router.post("/risk-library-deployments", response_model=DeployGlobalRisksResponse, status_code=status.HTTP_201_CREATED)
async def deploy_global_risks(
    body: DeployGlobalRisksRequest,
    service: Annotated[GlobalRiskService, Depends(get_global_risk_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str = Query(...),
) -> DeployGlobalRisksResponse:
    """Deploy global risks from the library to a workspace."""
    result = await service.deploy_global_risks(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        global_risk_ids=body.global_risk_ids,
    )
    return DeployGlobalRisksResponse(**result)


@router.delete("/risk-library-deployments/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_risk_deployment(
    deployment_id: str,
    service: Annotated[GlobalRiskService, Depends(get_global_risk_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Remove a risk library deployment."""
    await service.remove_risk_deployment(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        deployment_id=deployment_id,
    )

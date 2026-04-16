from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_control_mapping_service
from .schemas import (
    ApproveControlMappingRequest,
    AssignRiskToControlRequest,
    BulkApproveRequest,
    BulkRejectRequest,
    ControlMappingResponse,
    CreateControlMappingRequest,
    PendingMappingsResponse,
    RejectControlMappingRequest,
)
from .service import ControlMappingService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["risk-control-mappings"])


@router.get("/risks/{risk_id}/controls", response_model=list[ControlMappingResponse])
async def list_control_mappings(
    risk_id: str,
    service: Annotated[ControlMappingService, Depends(get_control_mapping_service)],
    claims=Depends(get_current_access_claims),
) -> list[ControlMappingResponse]:
    return await service.list_control_mappings(user_id=claims.subject, risk_id=risk_id)


@router.post(
    "/risks/{risk_id}/controls",
    response_model=ControlMappingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_control_mapping(
    risk_id: str,
    body: CreateControlMappingRequest,
    service: Annotated[ControlMappingService, Depends(get_control_mapping_service)],
    claims=Depends(get_current_access_claims),
) -> ControlMappingResponse:
    return await service.create_control_mapping(
        user_id=claims.subject, risk_id=risk_id, request=body
    )


@router.post(
    "/risks/{risk_id}/controls/{mapping_id}/approve",
    response_model=ControlMappingResponse,
)
async def approve_control_mapping(
    risk_id: str,
    mapping_id: str,
    body: ApproveControlMappingRequest,
    service: Annotated[ControlMappingService, Depends(get_control_mapping_service)],
    claims=Depends(get_current_access_claims),
) -> ControlMappingResponse:
    return await service.approve_control_mapping(
        user_id=claims.subject,
        risk_id=risk_id,
        mapping_id=mapping_id,
        request=body,
    )


@router.post(
    "/risks/{risk_id}/controls/{mapping_id}/reject",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reject_control_mapping(
    risk_id: str,
    mapping_id: str,
    body: RejectControlMappingRequest,
    service: Annotated[ControlMappingService, Depends(get_control_mapping_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.reject_control_mapping(
        user_id=claims.subject,
        risk_id=risk_id,
        mapping_id=mapping_id,
        request=body,
    )


@router.delete(
    "/risks/{risk_id}/controls/{mapping_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_control_mapping(
    risk_id: str,
    mapping_id: str,
    service: Annotated[ControlMappingService, Depends(get_control_mapping_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_control_mapping(
        user_id=claims.subject, risk_id=risk_id, mapping_id=mapping_id
    )


@router.get("/controls/{control_id}/risks", response_model=list[ControlMappingResponse])
async def list_risks_for_control(
    control_id: str,
    service: Annotated[ControlMappingService, Depends(get_control_mapping_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> list[ControlMappingResponse]:
    return await service.list_risks_for_control(user_id=claims.subject, control_id=control_id, org_id=org_id)


@router.post(
    "/controls/{control_id}/risks",
    response_model=ControlMappingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_risk_to_control(
    control_id: str,
    body: AssignRiskToControlRequest,
    service: Annotated[ControlMappingService, Depends(get_control_mapping_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> ControlMappingResponse:
    return await service.assign_risk_to_control(
        user_id=claims.subject, control_id=control_id, org_id=org_id, request=body
    )


# ── Cross-risk pending mappings (org-level approval queue) ─────────────────────

@router.get("/risks-controls/pending", response_model=PendingMappingsResponse)
async def list_pending_mappings(
    org_id: str = Query(...),
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=200, le=500),
    offset: int = Query(default=0),
    service: Annotated[ControlMappingService, Depends(get_control_mapping_service)] = ...,
    claims=Depends(get_current_access_claims),
) -> PendingMappingsResponse:
    return await service.list_pending_mappings(
        user_id=claims.subject,
        org_id=org_id,
        workspace_id=workspace_id,
        limit=limit,
        offset=offset,
    )


@router.post("/risks-controls/bulk-approve", response_model=dict)
async def bulk_approve_mappings(
    body: BulkApproveRequest,
    org_id: str = Query(...),
    service: Annotated[ControlMappingService, Depends(get_control_mapping_service)] = ...,
    claims=Depends(get_current_access_claims),
) -> dict:
    return await service.bulk_approve(
        user_id=claims.subject, org_id=org_id, request=body
    )


@router.post("/risks-controls/bulk-reject", response_model=dict)
async def bulk_reject_mappings(
    body: BulkRejectRequest,
    org_id: str = Query(...),
    service: Annotated[ControlMappingService, Depends(get_control_mapping_service)] = ...,
    claims=Depends(get_current_access_claims),
) -> dict:
    return await service.bulk_reject(
        user_id=claims.subject, org_id=org_id, request=body
    )

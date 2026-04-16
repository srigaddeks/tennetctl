from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_finding_service
from .service import FindingService

_schemas = import_module("backend.09_assessments.schemas")
CreateFindingRequest = _schemas.CreateFindingRequest
FindingListResponse = _schemas.FindingListResponse
FindingResponse = _schemas.FindingResponse
UpdateFindingRequest = _schemas.UpdateFindingRequest

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["findings"])


@router.post(
    "/assessments/{assessment_id}/findings",
    response_model=FindingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_finding(
    assessment_id: str,
    body: CreateFindingRequest,
    service: Annotated[FindingService, Depends(get_finding_service)],
    claims=Depends(get_current_access_claims),
) -> FindingResponse:
    return await service.create_finding(
        user_id=claims.subject,
        assessment_id=assessment_id,
        request=body,
    )


@router.get(
    "/assessments/{assessment_id}/findings",
    response_model=FindingListResponse,
)
async def list_findings(
    assessment_id: str,
    service: Annotated[FindingService, Depends(get_finding_service)],
    claims=Depends(get_current_access_claims),
    severity_code: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    finding_type: str | None = Query(None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> FindingListResponse:
    return await service.list_findings(
        user_id=claims.subject,
        assessment_id=assessment_id,
        severity_code=severity_code,
        status_code=status_filter,
        finding_type=finding_type,
        limit=limit,
        offset=offset,
    )


@router.patch("/findings/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: str,
    body: UpdateFindingRequest,
    service: Annotated[FindingService, Depends(get_finding_service)],
    claims=Depends(get_current_access_claims),
) -> FindingResponse:
    return await service.update_finding(
        user_id=claims.subject,
        finding_id=finding_id,
        request=body,
    )


@router.delete("/findings/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_finding(
    finding_id: str,
    service: Annotated[FindingService, Depends(get_finding_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_finding(
        user_id=claims.subject,
        finding_id=finding_id,
    )

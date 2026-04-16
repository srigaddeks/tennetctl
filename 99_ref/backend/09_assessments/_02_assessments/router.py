from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_assessment_service
from .service import AssessmentService

_schemas = import_module("backend.09_assessments.schemas")
AssessmentListResponse = _schemas.AssessmentListResponse
AssessmentResponse = _schemas.AssessmentResponse
AssessmentSummaryResponse = _schemas.AssessmentSummaryResponse
CreateAssessmentRequest = _schemas.CreateAssessmentRequest
UpdateAssessmentRequest = _schemas.UpdateAssessmentRequest

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["assessments"])


@router.post(
    "/assessments",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assessment(
    body: CreateAssessmentRequest,
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
    claims=Depends(get_current_access_claims),
) -> AssessmentResponse:
    return await service.create_assessment(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=body,
    )


@router.get("/assessments", response_model=AssessmentListResponse)
async def list_assessments(
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(None),
    workspace_id: str | None = Query(None),
    type_code: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> AssessmentListResponse:
    return await service.list_assessments(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        type_code=type_code,
        status_code=status_filter,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/assessments/{assessment_id}/summary", response_model=AssessmentSummaryResponse)
async def get_assessment_summary(
    assessment_id: str,
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
    claims=Depends(get_current_access_claims),
) -> AssessmentSummaryResponse:
    return await service.get_summary(
        user_id=claims.subject,
        assessment_id=assessment_id,
    )


@router.post(
    "/assessments/{assessment_id}/complete",
    response_model=AssessmentResponse,
)
async def complete_assessment(
    assessment_id: str,
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
    claims=Depends(get_current_access_claims),
) -> AssessmentResponse:
    return await service.complete_assessment(
        user_id=claims.subject,
        assessment_id=assessment_id,
    )


@router.get("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
    claims=Depends(get_current_access_claims),
) -> AssessmentResponse:
    return await service.get_assessment(
        user_id=claims.subject,
        assessment_id=assessment_id,
    )


@router.patch("/assessments/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: str,
    body: UpdateAssessmentRequest,
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
    claims=Depends(get_current_access_claims),
) -> AssessmentResponse:
    return await service.update_assessment(
        user_id=claims.subject,
        assessment_id=assessment_id,
        request=body,
    )


@router.delete(
    "/assessments/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_assessment(
    assessment_id: str,
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_assessment(
        user_id=claims.subject,
        assessment_id=assessment_id,
    )

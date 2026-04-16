from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, status

from .dependencies import get_assessment_service
from .schemas import AssessmentResponse, CreateAssessmentRequest
from .service import AssessmentService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["risk-assessments"])


@router.get("/risks/{risk_id}/assessments", response_model=list[AssessmentResponse])
async def list_assessments(
    risk_id: str,
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
    claims=Depends(get_current_access_claims),
) -> list[AssessmentResponse]:
    return await service.list_assessments(user_id=claims.subject, risk_id=risk_id)


@router.post(
    "/risks/{risk_id}/assessments",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assessment(
    risk_id: str,
    body: CreateAssessmentRequest,
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
    claims=Depends(get_current_access_claims),
) -> AssessmentResponse:
    return await service.create_assessment(
        user_id=claims.subject, risk_id=risk_id, request=body
    )

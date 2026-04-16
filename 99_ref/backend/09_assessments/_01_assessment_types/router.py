from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends

from .dependencies import get_assessment_types_service
from .service import AssessmentTypesService

_schemas_module = import_module("backend.09_assessments.schemas")
DimensionListResponse = _schemas_module.DimensionListResponse

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["assessment-types"])


@router.get("/assessments/types", response_model=DimensionListResponse)
async def list_assessment_types(
    service: Annotated[AssessmentTypesService, Depends(get_assessment_types_service)],
    claims=Depends(get_current_access_claims),
) -> DimensionListResponse:
    return await service.list_assessment_types()


@router.get("/assessments/statuses", response_model=DimensionListResponse)
async def list_assessment_statuses(
    service: Annotated[AssessmentTypesService, Depends(get_assessment_types_service)],
    claims=Depends(get_current_access_claims),
) -> DimensionListResponse:
    return await service.list_assessment_statuses()


@router.get("/assessments/finding-severities", response_model=DimensionListResponse)
async def list_finding_severities(
    service: Annotated[AssessmentTypesService, Depends(get_assessment_types_service)],
    claims=Depends(get_current_access_claims),
) -> DimensionListResponse:
    return await service.list_finding_severities()


@router.get("/assessments/finding-statuses", response_model=DimensionListResponse)
async def list_finding_statuses(
    service: Annotated[AssessmentTypesService, Depends(get_assessment_types_service)],
    claims=Depends(get_current_access_claims),
) -> DimensionListResponse:
    return await service.list_finding_statuses()

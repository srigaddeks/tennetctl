from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, status

from .dependencies import get_finding_response_service
from .service import FindingResponseService

_schemas = import_module("backend.09_assessments.schemas")
CreateFindingResponseRequest = _schemas.CreateFindingResponseRequest
FindingResponseListResponse = _schemas.FindingResponseListResponse
FindingResponseResponse = _schemas.FindingResponseResponse

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["finding-responses"])


@router.post(
    "/findings/{finding_id}/responses",
    response_model=FindingResponseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_finding_response(
    finding_id: str,
    body: CreateFindingResponseRequest,
    service: Annotated[FindingResponseService, Depends(get_finding_response_service)],
    claims=Depends(get_current_access_claims),
) -> FindingResponseResponse:
    return await service.create_response(
        user_id=claims.subject,
        finding_id=finding_id,
        request=body,
    )


@router.get(
    "/findings/{finding_id}/responses",
    response_model=FindingResponseListResponse,
)
async def list_finding_responses(
    finding_id: str,
    service: Annotated[FindingResponseService, Depends(get_finding_response_service)],
    claims=Depends(get_current_access_claims),
) -> FindingResponseListResponse:
    return await service.list_responses(
        user_id=claims.subject,
        finding_id=finding_id,
    )

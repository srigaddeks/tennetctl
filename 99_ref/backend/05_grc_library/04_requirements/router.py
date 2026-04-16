from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_requirement_service
from .schemas import (
    CreateRequirementRequest,
    RequirementListResponse,
    RequirementResponse,
    UpdateRequirementRequest,
)
from .service import RequirementService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/fr", tags=["grc-requirements"])


@router.get(
    "/frameworks/{framework_id}/requirements", response_model=RequirementListResponse
)
async def list_requirements(
    framework_id: str,
    service: Annotated[RequirementService, Depends(get_requirement_service)],
    claims=Depends(get_current_access_claims),
    version_id: str | None = Query(default=None),
) -> RequirementListResponse:
    return await service.list_requirements(
        user_id=claims.subject, framework_id=framework_id, version_id=version_id
    )


@router.post(
    "/frameworks/{framework_id}/requirements",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_requirement(
    framework_id: str,
    body: CreateRequirementRequest,
    service: Annotated[RequirementService, Depends(get_requirement_service)],
    claims=Depends(get_current_access_claims),
) -> RequirementResponse:
    return await service.create_requirement(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        request=body,
    )


@router.patch(
    "/frameworks/{framework_id}/requirements/{requirement_id}",
    response_model=RequirementResponse,
)
async def update_requirement(
    framework_id: str,
    requirement_id: str,
    body: UpdateRequirementRequest,
    service: Annotated[RequirementService, Depends(get_requirement_service)],
    claims=Depends(get_current_access_claims),
) -> RequirementResponse:
    return await service.update_requirement(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        requirement_id=requirement_id,
        request=body,
    )


@router.delete(
    "/frameworks/{framework_id}/requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_requirement(
    framework_id: str,
    requirement_id: str,
    service: Annotated[RequirementService, Depends(get_requirement_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_requirement(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        requirement_id=requirement_id,
    )

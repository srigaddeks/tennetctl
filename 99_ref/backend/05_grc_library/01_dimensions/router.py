from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends

from .dependencies import get_dimension_service
from .schemas import DimensionResponse
from .service import DimensionService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/fr", tags=["grc-dimensions"])


@router.get("/framework-types", response_model=list[DimensionResponse])
async def list_framework_types(
    service: Annotated[DimensionService, Depends(get_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[DimensionResponse]:
    return await service.list_dimension(dimension_name="framework_types")


@router.get("/framework-categories", response_model=list[DimensionResponse])
async def list_framework_categories(
    service: Annotated[DimensionService, Depends(get_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[DimensionResponse]:
    return await service.list_dimension(dimension_name="framework_categories")


@router.get("/control-categories", response_model=list[DimensionResponse])
async def list_control_categories(
    service: Annotated[DimensionService, Depends(get_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[DimensionResponse]:
    return await service.list_dimension(dimension_name="control_categories")


@router.get("/control-criticalities", response_model=list[DimensionResponse])
async def list_control_criticalities(
    service: Annotated[DimensionService, Depends(get_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[DimensionResponse]:
    return await service.list_dimension(dimension_name="control_criticalities")


@router.get("/test-types", response_model=list[DimensionResponse])
async def list_test_types(
    service: Annotated[DimensionService, Depends(get_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[DimensionResponse]:
    return await service.list_dimension(dimension_name="test_types")


@router.get("/test-result-statuses", response_model=list[DimensionResponse])
async def list_test_result_statuses(
    service: Annotated[DimensionService, Depends(get_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[DimensionResponse]:
    return await service.list_dimension(dimension_name="test_result_statuses")

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends

from .dependencies import get_dimensions_service
from .schemas import RiskCategoryResponse, RiskLevelResponse, RiskTreatmentTypeResponse
from .service import DimensionsService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["risk-dimensions"])


@router.get("/risk-categories", response_model=list[RiskCategoryResponse])
async def list_risk_categories(
    service: Annotated[DimensionsService, Depends(get_dimensions_service)],
    claims=Depends(get_current_access_claims),
) -> list[RiskCategoryResponse]:
    return await service.list_risk_categories()


@router.get("/treatment-types", response_model=list[RiskTreatmentTypeResponse])
async def list_treatment_types(
    service: Annotated[DimensionsService, Depends(get_dimensions_service)],
    claims=Depends(get_current_access_claims),
) -> list[RiskTreatmentTypeResponse]:
    return await service.list_treatment_types()


@router.get("/risk-levels", response_model=list[RiskLevelResponse])
async def list_risk_levels(
    service: Annotated[DimensionsService, Depends(get_dimensions_service)],
    claims=Depends(get_current_access_claims),
) -> list[RiskLevelResponse]:
    return await service.list_risk_levels()

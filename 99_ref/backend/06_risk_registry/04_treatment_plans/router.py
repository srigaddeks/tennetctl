from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, status

from .dependencies import get_treatment_plan_service
from .schemas import (
    CreateTreatmentPlanRequest,
    TreatmentPlanResponse,
    UpdateTreatmentPlanRequest,
)
from .service import TreatmentPlanService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["risk-treatment-plans"])


@router.get("/risks/{risk_id}/treatment-plan", response_model=TreatmentPlanResponse | None)
async def get_treatment_plan(
    risk_id: str,
    service: Annotated[TreatmentPlanService, Depends(get_treatment_plan_service)],
    claims=Depends(get_current_access_claims),
) -> TreatmentPlanResponse | None:
    return await service.get_treatment_plan(user_id=claims.subject, risk_id=risk_id)


@router.post(
    "/risks/{risk_id}/treatment-plan",
    response_model=TreatmentPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_treatment_plan(
    risk_id: str,
    body: CreateTreatmentPlanRequest,
    service: Annotated[TreatmentPlanService, Depends(get_treatment_plan_service)],
    claims=Depends(get_current_access_claims),
) -> TreatmentPlanResponse:
    return await service.create_treatment_plan(
        user_id=claims.subject, risk_id=risk_id, request=body
    )


@router.patch("/risks/{risk_id}/treatment-plan", response_model=TreatmentPlanResponse)
async def update_treatment_plan(
    risk_id: str,
    body: UpdateTreatmentPlanRequest,
    service: Annotated[TreatmentPlanService, Depends(get_treatment_plan_service)],
    claims=Depends(get_current_access_claims),
) -> TreatmentPlanResponse:
    return await service.update_treatment_plan(
        user_id=claims.subject, risk_id=risk_id, request=body
    )

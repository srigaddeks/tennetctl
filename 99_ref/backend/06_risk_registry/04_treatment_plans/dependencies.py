from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.06_risk_registry.04_treatment_plans.service")
TreatmentPlanService = _service_module.TreatmentPlanService


def get_treatment_plan_service(request: Request) -> TreatmentPlanService:
    return TreatmentPlanService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

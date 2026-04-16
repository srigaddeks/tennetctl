from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.06_risk_registry.03_assessments.service")
AssessmentService = _service_module.AssessmentService


def get_assessment_service(request: Request) -> AssessmentService:
    return AssessmentService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

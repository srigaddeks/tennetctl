from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.09_assessments._01_assessment_types.service")
AssessmentTypesService = _service_module.AssessmentTypesService


def get_assessment_types_service(request: Request) -> AssessmentTypesService:
    return AssessmentTypesService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

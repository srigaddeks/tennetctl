from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.09_assessments._04_finding_responses.service")
FindingResponseService = _service_module.FindingResponseService


def get_finding_response_service(request: Request) -> FindingResponseService:
    return FindingResponseService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.09_assessments._03_findings.service")
FindingService = _service_module.FindingService


def get_finding_service(request: Request) -> FindingService:
    return FindingService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

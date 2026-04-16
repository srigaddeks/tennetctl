from __future__ import annotations
from importlib import import_module
from fastapi import Request
_service_module = import_module("backend.20_ai.07_reporting.service")
ReportingService = _service_module.ReportingService

def get_reporting_service(request: Request) -> ReportingService:
    return ReportingService(settings=request.app.state.settings,
        database_pool=request.app.state.database_pool, cache=request.app.state.cache)

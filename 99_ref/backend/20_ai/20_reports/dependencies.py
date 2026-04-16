from __future__ import annotations

from importlib import import_module

from fastapi import Request

_svc_module = import_module("backend.20_ai.20_reports.service")
ReportService = _svc_module.ReportService


def get_report_service(request: Request) -> ReportService:
    return ReportService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

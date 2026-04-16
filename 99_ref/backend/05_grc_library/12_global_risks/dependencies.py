from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.05_grc_library.12_global_risks.service")
GlobalRiskService = _service_module.GlobalRiskService


def get_global_risk_service(request: Request) -> GlobalRiskService:
    return GlobalRiskService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

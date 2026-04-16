from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.06_risk_registry.02_risks.service")
RiskService = _service_module.RiskService


def get_risk_service(request: Request) -> RiskService:
    return RiskService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

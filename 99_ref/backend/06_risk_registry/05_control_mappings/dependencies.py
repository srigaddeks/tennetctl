from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.06_risk_registry.05_control_mappings.service")
ControlMappingService = _service_module.ControlMappingService


def get_control_mapping_service(request: Request) -> ControlMappingService:
    return ControlMappingService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

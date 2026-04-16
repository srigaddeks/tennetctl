from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.06_risk_registry.01_dimensions.service")
DimensionsService = _service_module.DimensionsService


def get_dimensions_service(request: Request) -> DimensionsService:
    return DimensionsService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

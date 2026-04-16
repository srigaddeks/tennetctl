from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.05_grc_library.01_dimensions.service")
DimensionService = _service_module.DimensionService


def get_dimension_service(request: Request) -> DimensionService:
    return DimensionService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

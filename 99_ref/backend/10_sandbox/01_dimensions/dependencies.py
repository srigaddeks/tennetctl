from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.01_dimensions.service")
SandboxDimensionService = _service_module.SandboxDimensionService


def get_sandbox_dimension_service(request: Request) -> SandboxDimensionService:
    return SandboxDimensionService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

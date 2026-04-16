from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.05_grc_library.02_frameworks.service")
FrameworkService = _service_module.FrameworkService


def get_framework_service(request: Request) -> FrameworkService:
    return FrameworkService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

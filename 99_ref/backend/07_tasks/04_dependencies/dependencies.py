from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.07_tasks.04_dependencies.service")
DependencyService = _service_module.DependencyService


def get_dependency_service(request: Request) -> DependencyService:
    return DependencyService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

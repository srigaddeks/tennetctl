from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.06_access_context.service")
AccessContextService = _service_module.AccessContextService


def get_access_context_service(request: Request) -> AccessContextService:
    return AccessContextService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

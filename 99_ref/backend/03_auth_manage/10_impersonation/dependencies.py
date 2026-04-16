from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.10_impersonation.service")
ImpersonationService = _service_module.ImpersonationService


def get_impersonation_service(request: Request) -> ImpersonationService:
    return ImpersonationService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

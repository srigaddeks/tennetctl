from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.11_admin.service")
AdminService = _service_module.AdminService


def get_admin_service(request: Request) -> AdminService:
    return AdminService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

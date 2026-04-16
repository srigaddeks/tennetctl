from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.04_roles.service")
RoleService = _service_module.RoleService


def get_role_service(request: Request) -> RoleService:
    return RoleService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

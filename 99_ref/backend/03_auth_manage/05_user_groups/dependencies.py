from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.05_user_groups.service")
UserGroupService = _service_module.UserGroupService


def get_user_group_service(request: Request) -> UserGroupService:
    return UserGroupService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

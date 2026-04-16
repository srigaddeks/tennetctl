from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.08_workspaces.service")
WorkspaceService = _service_module.WorkspaceService


def get_workspace_service(request: Request) -> WorkspaceService:
    return WorkspaceService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

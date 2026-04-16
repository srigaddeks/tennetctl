from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.16_portal_views.service")
PortalViewService = _service_module.PortalViewService


def get_portal_view_service(request: Request) -> PortalViewService:
    return PortalViewService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

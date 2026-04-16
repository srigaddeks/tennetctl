from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.07_orgs.service")
OrgService = _service_module.OrgService


def get_org_service(request: Request) -> OrgService:
    return OrgService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

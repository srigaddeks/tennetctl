from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.13_api_keys.service")
ApiKeyService = _service_module.ApiKeyService


def get_api_key_service(request: Request) -> ApiKeyService:
    return ApiKeyService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

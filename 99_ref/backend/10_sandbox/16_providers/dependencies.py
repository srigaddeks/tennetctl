from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.16_providers.service")
ProviderService = _service_module.ProviderService


def get_provider_service(request: Request) -> ProviderService:
    return ProviderService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

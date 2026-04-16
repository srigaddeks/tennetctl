from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.14_assets.service")
AssetService = _service_module.AssetService


def get_asset_service(request: Request) -> AssetService:
    return AssetService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

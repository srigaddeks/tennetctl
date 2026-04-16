from __future__ import annotations

from importlib import import_module

from fastapi import Request

from .service import AssetConnectorService


def get_asset_connector_service(request: Request) -> AssetConnectorService:
    _settings_module = import_module("backend.00_config.settings")
    return AssetConnectorService(
        settings=_settings_module.load_settings(),
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

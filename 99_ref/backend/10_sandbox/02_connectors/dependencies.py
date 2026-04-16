from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.02_connectors.service")
ConnectorService = _service_module.ConnectorService


def get_connector_service(request: Request) -> ConnectorService:
    return ConnectorService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

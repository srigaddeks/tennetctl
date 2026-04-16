from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.04_notifications.06_broadcasts.service")
BroadcastService = _service_module.BroadcastService


def get_broadcast_service(request: Request) -> BroadcastService:
    return BroadcastService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

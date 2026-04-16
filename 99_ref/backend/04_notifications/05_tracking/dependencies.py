from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.04_notifications.05_tracking.service")
TrackingService = _service_module.TrackingService


def get_tracking_service(request: Request) -> TrackingService:
    return TrackingService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

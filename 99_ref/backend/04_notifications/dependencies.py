from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.04_notifications.service")
NotificationService = _service_module.NotificationService


def get_notification_service(request: Request) -> NotificationService:
    return NotificationService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.07_tasks.05_events.service")
EventService = _service_module.EventService


def get_event_service(request: Request) -> EventService:
    return EventService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.06_risk_registry.06_review_events.service")
ReviewEventService = _service_module.ReviewEventService


def get_review_event_service(request: Request) -> ReviewEventService:
    return ReviewEventService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

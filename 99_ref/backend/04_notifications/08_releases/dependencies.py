from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.04_notifications.08_releases.service")
ReleaseIncidentService = _service_module.ReleaseIncidentService


def get_release_incident_service(request: Request) -> ReleaseIncidentService:
    return ReleaseIncidentService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

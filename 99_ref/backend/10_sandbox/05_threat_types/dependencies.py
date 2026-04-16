from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.05_threat_types.service")
ThreatTypeService = _service_module.ThreatTypeService


def get_threat_type_service(request: Request) -> ThreatTypeService:
    return ThreatTypeService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

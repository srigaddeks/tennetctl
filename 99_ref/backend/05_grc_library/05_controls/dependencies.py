from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.05_grc_library.05_controls.service")
ControlService = _service_module.ControlService


def get_control_service(request: Request) -> ControlService:
    return ControlService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

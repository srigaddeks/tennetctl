from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.05_grc_library.04_requirements.service")
RequirementService = _service_module.RequirementService


def get_requirement_service(request: Request) -> RequirementService:
    return RequirementService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

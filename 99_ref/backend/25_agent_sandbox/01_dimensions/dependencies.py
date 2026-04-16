from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.25_agent_sandbox.01_dimensions.service")
AgentSandboxDimensionService = _service_module.AgentSandboxDimensionService


def get_agent_sandbox_dimension_service(request: Request) -> AgentSandboxDimensionService:
    return AgentSandboxDimensionService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

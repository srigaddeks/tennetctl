from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.25_agent_sandbox.03_tools.service")
AgentToolService = _service_module.AgentToolService


def get_agent_tool_service(request: Request) -> AgentToolService:
    return AgentToolService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

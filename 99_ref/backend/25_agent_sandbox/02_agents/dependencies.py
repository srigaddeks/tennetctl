from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.25_agent_sandbox.02_agents.service")
AgentService = _service_module.AgentService


def get_agent_service(request: Request) -> AgentService:
    return AgentService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

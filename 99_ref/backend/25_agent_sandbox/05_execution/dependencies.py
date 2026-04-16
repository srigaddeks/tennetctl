from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.25_agent_sandbox.05_execution.service")
AgentExecutionService = _service_module.AgentExecutionService


def get_agent_execution_service(request: Request) -> AgentExecutionService:
    return AgentExecutionService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

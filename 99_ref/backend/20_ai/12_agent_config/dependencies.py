from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.20_ai.12_agent_config.service")
AgentConfigService = _service_module.AgentConfigService


def get_agent_config_service(request: Request) -> AgentConfigService:
    return AgentConfigService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

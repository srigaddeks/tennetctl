from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.20_ai.13_prompt_config.service")
PromptConfigService = _service_module.PromptConfigService


def get_prompt_config_service(request: Request) -> PromptConfigService:
    return PromptConfigService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

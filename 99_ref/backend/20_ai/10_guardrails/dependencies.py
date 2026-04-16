from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.20_ai.10_guardrails.service")
GuardrailService = _service_module.GuardrailService


def get_guardrail_service(request: Request) -> GuardrailService:
    return GuardrailService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

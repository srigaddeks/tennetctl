from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.04_notifications.07_rules.service")
RuleService = _service_module.RuleService


def get_rule_service(request: Request) -> RuleService:
    return RuleService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

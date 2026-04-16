from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.04_notifications.09_variable_queries.service")
VariableQueryService = _service_module.VariableQueryService


def get_variable_query_service(request: Request) -> VariableQueryService:
    return VariableQueryService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

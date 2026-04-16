from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.07_execution.service")
ExecutionService = _service_module.ExecutionService


def get_execution_service(request: Request) -> ExecutionService:
    return ExecutionService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
        clickhouse=request.app.state.clickhouse,
    )

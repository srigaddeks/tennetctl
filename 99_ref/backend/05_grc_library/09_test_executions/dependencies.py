from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.05_grc_library.09_test_executions.service")
TestExecutionService = _service_module.TestExecutionService


def get_test_execution_service(request: Request) -> TestExecutionService:
    return TestExecutionService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

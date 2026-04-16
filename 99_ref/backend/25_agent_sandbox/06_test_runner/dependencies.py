from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.25_agent_sandbox.06_test_runner.service")
TestRunnerService = _service_module.TestRunnerService


def get_test_runner_service(request: Request) -> TestRunnerService:
    return TestRunnerService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

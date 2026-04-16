from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.25_agent_sandbox.04_test_scenarios.service")
TestScenarioService = _service_module.TestScenarioService


def get_test_scenario_service(request: Request) -> TestScenarioService:
    return TestScenarioService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

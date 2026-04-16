from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.23_global_control_tests.service")
GlobalControlTestService = _service_module.GlobalControlTestService


def get_global_control_test_service(request: Request) -> GlobalControlTestService:
    return GlobalControlTestService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

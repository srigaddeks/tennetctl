from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.05_grc_library.06_tests.service")
TestService = _service_module.TestService


def get_test_service(request: Request) -> TestService:
    return TestService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

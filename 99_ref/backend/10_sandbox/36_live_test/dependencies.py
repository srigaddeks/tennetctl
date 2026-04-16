from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.36_live_test.service")
LiveTestService = _service_module.LiveTestService


def get_live_test_service(request: Request) -> LiveTestService:
    return LiveTestService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

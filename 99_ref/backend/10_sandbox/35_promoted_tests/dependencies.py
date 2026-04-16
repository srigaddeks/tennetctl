from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.35_promoted_tests.service")
PromotedTestService = _service_module.PromotedTestService


def get_promoted_test_service(request: Request) -> PromotedTestService:
    return PromotedTestService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

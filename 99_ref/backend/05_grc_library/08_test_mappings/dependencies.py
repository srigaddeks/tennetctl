from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.05_grc_library.08_test_mappings.service")
TestMappingService = _service_module.TestMappingService


def get_test_mapping_service(request: Request) -> TestMappingService:
    return TestMappingService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

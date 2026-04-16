from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.09_libraries.service")
LibraryService = _service_module.LibraryService


def get_library_service(request: Request) -> LibraryService:
    return LibraryService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

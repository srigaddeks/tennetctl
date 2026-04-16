from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.05_grc_library.03_versions.service")
VersionService = _service_module.VersionService


def get_version_service(request: Request) -> VersionService:
    return VersionService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.05_grc_library.10_settings.service")
FrameworkSettingService = _service_module.FrameworkSettingService


def get_framework_setting_service(request: Request) -> FrameworkSettingService:
    return FrameworkSettingService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

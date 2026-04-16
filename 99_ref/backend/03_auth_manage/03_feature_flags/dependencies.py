from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.03_feature_flags.service")
FeatureFlagService = _service_module.FeatureFlagService


def get_feature_flag_service(request: Request) -> FeatureFlagService:
    return FeatureFlagService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

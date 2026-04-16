from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.14_license_profiles.service")
LicenseProfileService = _service_module.LicenseProfileService


def get_license_profile_service(request: Request) -> LicenseProfileService:
    return LicenseProfileService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

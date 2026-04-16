"""Dependency injection for the generic entity settings service."""

from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_mod = import_module("backend.03_auth_manage.12_entity_settings.service")
EntitySettingsService = _service_mod.EntitySettingsService


def get_entity_settings_service(request: Request) -> EntitySettingsService:
    return EntitySettingsService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

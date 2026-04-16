from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.04_notifications.01_templates.service")
TemplateService = _service_module.TemplateService


def get_template_service(request: Request) -> TemplateService:
    return TemplateService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

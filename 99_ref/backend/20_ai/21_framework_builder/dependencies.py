"""FastAPI dependency injection for the Framework Builder module."""

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Request

_database_module = import_module("backend.01_core.database")
_svc_module = import_module("backend.20_ai.21_framework_builder.service")

DatabasePool = _database_module.DatabasePool
FrameworkBuilderService = _svc_module.FrameworkBuilderService


def get_framework_builder_service(request: Request) -> FrameworkBuilderService:
    return FrameworkBuilderService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
    )

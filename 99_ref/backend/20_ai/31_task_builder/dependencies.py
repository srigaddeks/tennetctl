from __future__ import annotations

from importlib import import_module

from fastapi import Request


_svc_module = import_module("backend.20_ai.31_task_builder.service")
TaskBuilderService = _svc_module.TaskBuilderService


def get_task_builder_service(request: Request) -> TaskBuilderService:
    return TaskBuilderService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

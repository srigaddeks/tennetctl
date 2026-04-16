from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.07_tasks.02_tasks.service")
TaskService = _service_module.TaskService


def get_task_service(request: Request) -> TaskService:
    return TaskService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

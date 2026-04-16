from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.07_tasks.03_assignments.service")
AssignmentService = _service_module.AssignmentService


def get_assignment_service(request: Request) -> AssignmentService:
    return AssignmentService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

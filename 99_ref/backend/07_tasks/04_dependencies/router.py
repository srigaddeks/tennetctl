from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, status

from .dependencies import get_dependency_service
from .schemas import AddDependencyRequest, TaskDependencyListResponse, TaskDependencyResponse
from .service import DependencyService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["task-dependencies"])


@router.get("/tasks/{task_id}/dependencies", response_model=TaskDependencyListResponse)
async def list_task_dependencies(
    task_id: str,
    service: Annotated[DependencyService, Depends(get_dependency_service)],
    claims=Depends(get_current_access_claims),
) -> TaskDependencyListResponse:
    return await service.list_dependencies(user_id=claims.subject, task_id=task_id)


@router.post(
    "/tasks/{task_id}/dependencies",
    response_model=TaskDependencyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_task_dependency(
    task_id: str,
    body: AddDependencyRequest,
    service: Annotated[DependencyService, Depends(get_dependency_service)],
    claims=Depends(get_current_access_claims),
) -> TaskDependencyResponse:
    return await service.add_dependency(
        user_id=claims.subject, task_id=task_id, request=body
    )


@router.delete(
    "/tasks/{task_id}/dependencies/{dependency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_task_dependency(
    task_id: str,
    dependency_id: str,
    service: Annotated[DependencyService, Depends(get_dependency_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.remove_dependency(
        user_id=claims.subject, task_id=task_id, dependency_id=dependency_id
    )

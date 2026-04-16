from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends

from .dependencies import get_dimension_service
from .schemas import TaskPriorityResponse, TaskStatusResponse, TaskTypeResponse
from .service import DimensionService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["task-dimensions"])


@router.get("/task-types", response_model=list[TaskTypeResponse])
async def list_task_types(
    service: Annotated[DimensionService, Depends(get_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[TaskTypeResponse]:
    return await service.list_task_types()


@router.get("/task-priorities", response_model=list[TaskPriorityResponse])
async def list_task_priorities(
    service: Annotated[DimensionService, Depends(get_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[TaskPriorityResponse]:
    return await service.list_task_priorities()


@router.get("/task-statuses", response_model=list[TaskStatusResponse])
async def list_task_statuses(
    service: Annotated[DimensionService, Depends(get_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[TaskStatusResponse]:
    return await service.list_task_statuses()

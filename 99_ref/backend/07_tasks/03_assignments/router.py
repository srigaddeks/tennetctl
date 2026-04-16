from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, status

from .dependencies import get_assignment_service
from .schemas import AddAssignmentRequest, TaskAssignmentResponse
from .service import AssignmentService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["task-assignments"])


@router.get("/tasks/{task_id}/assignments", response_model=list[TaskAssignmentResponse])
async def list_task_assignments(
    task_id: str,
    service: Annotated[AssignmentService, Depends(get_assignment_service)],
    claims=Depends(get_current_access_claims),
) -> list[TaskAssignmentResponse]:
    return await service.list_assignments(user_id=claims.subject, task_id=task_id)


@router.post(
    "/tasks/{task_id}/assignments",
    response_model=TaskAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_task_assignment(
    task_id: str,
    body: AddAssignmentRequest,
    service: Annotated[AssignmentService, Depends(get_assignment_service)],
    claims=Depends(get_current_access_claims),
) -> TaskAssignmentResponse:
    return await service.add_assignment(
        user_id=claims.subject, task_id=task_id, request=body
    )


@router.delete(
    "/tasks/{task_id}/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_task_assignment(
    task_id: str,
    assignment_id: str,
    service: Annotated[AssignmentService, Depends(get_assignment_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.remove_assignment(
        user_id=claims.subject, task_id=task_id, assignment_id=assignment_id
    )

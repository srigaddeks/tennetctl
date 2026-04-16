from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, status

from .dependencies import get_event_service
from .schemas import AddCommentRequest, TaskEventListResponse, TaskEventResponse
from .service import EventService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["task-events"])


@router.get("/tasks/{task_id}/events", response_model=TaskEventListResponse)
async def list_task_events(
    task_id: str,
    service: Annotated[EventService, Depends(get_event_service)],
    claims=Depends(get_current_access_claims),
) -> TaskEventListResponse:
    return await service.list_events(user_id=claims.subject, task_id=task_id)


@router.post(
    "/tasks/{task_id}/events",
    response_model=TaskEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_task_comment(
    task_id: str,
    body: AddCommentRequest,
    service: Annotated[EventService, Depends(get_event_service)],
    claims=Depends(get_current_access_claims),
) -> TaskEventResponse:
    return await service.add_comment(
        user_id=claims.subject, task_id=task_id, request=body
    )

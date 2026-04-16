from __future__ import annotations

from pydantic import BaseModel


class AddDependencyRequest(BaseModel):
    blocking_task_id: str


class TaskDependencyResponse(BaseModel):
    id: str
    blocking_task_id: str
    blocked_task_id: str
    created_at: str
    created_by: str | None = None


class TaskDependencyListResponse(BaseModel):
    blockers: list[TaskDependencyResponse]
    blocked_by: list[TaskDependencyResponse]

from __future__ import annotations

from pydantic import BaseModel, Field


class AddCommentRequest(BaseModel):
    comment: str = Field(..., min_length=1, max_length=5000)


class TaskEventResponse(BaseModel):
    id: str
    task_id: str
    event_type: str
    old_value: str | None = None
    new_value: str | None = None
    comment: str | None = None
    actor_id: str
    occurred_at: str


class TaskEventListResponse(BaseModel):
    items: list[TaskEventResponse]
    total: int

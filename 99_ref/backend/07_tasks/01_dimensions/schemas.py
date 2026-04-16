from __future__ import annotations

from pydantic import BaseModel


class TaskTypeResponse(BaseModel):
    code: str
    name: str
    description: str
    sort_order: int


class TaskPriorityResponse(BaseModel):
    code: str
    name: str
    description: str
    sort_order: int


class TaskStatusResponse(BaseModel):
    code: str
    name: str
    description: str
    is_terminal: bool
    sort_order: int

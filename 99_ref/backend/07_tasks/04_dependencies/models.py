from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskDependencyRecord:
    id: str
    blocking_task_id: str
    blocked_task_id: str
    created_at: str
    created_by: str | None

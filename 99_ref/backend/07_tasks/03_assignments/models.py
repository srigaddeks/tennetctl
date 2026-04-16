from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskAssignmentRecord:
    id: str
    task_id: str
    user_id: str
    role: str
    assigned_at: str
    assigned_by: str | None

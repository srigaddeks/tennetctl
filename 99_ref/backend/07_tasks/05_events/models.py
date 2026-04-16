from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskEventRecord:
    id: str
    task_id: str
    event_type: str
    old_value: str | None
    new_value: str | None
    comment: str | None
    actor_id: str
    occurred_at: str

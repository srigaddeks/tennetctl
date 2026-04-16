from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewEventRecord:
    id: str
    risk_id: str
    event_type: str
    old_status: str | None
    new_status: str | None
    actor_id: str
    comment: str | None
    occurred_at: str

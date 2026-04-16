from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RequirementRecord:
    id: str
    framework_id: str
    requirement_code: str
    sort_order: int
    parent_requirement_id: str | None
    is_active: bool
    created_at: str
    updated_at: str
    # EAV properties
    name: str | None = None
    description: str | None = None

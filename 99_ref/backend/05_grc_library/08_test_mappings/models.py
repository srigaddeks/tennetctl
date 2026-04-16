from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TestMappingRecord:
    id: str
    control_test_id: str
    control_id: str
    is_primary: bool
    sort_order: int
    created_at: str
    created_by: str | None
    # Joined fields
    control_code: str | None = None
    control_name: str | None = None
    framework_code: str | None = None

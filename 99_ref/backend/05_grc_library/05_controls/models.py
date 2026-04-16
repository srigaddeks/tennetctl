from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControlDetailRecord:
    id: str
    framework_id: str
    requirement_id: str | None
    tenant_key: str
    control_code: str
    control_category_code: str
    category_name: str | None
    criticality_code: str
    criticality_name: str | None
    control_type: str
    automation_potential: str
    sort_order: int
    version: int
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None
    description: str | None
    guidance: str | None
    implementation_notes: str | None
    framework_code: str | None
    framework_name: str | None
    requirement_code: str | None
    requirement_name: str | None
    test_count: int

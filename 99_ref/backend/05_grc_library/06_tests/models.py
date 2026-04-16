from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TestDetailRecord:
    id: str
    tenant_key: str
    test_code: str
    test_type_code: str
    test_type_name: str | None
    integration_type: str | None
    monitoring_frequency: str
    is_platform_managed: bool
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None
    description: str | None
    evaluation_rule: str | None
    signal_type: str | None
    integration_guide: str | None
    mapped_control_count: int
    scope_org_id: str | None
    scope_workspace_id: str | None

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromotedTestRecord:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None
    promotion_id: str | None
    source_signal_id: str | None
    source_policy_id: str | None
    source_library_id: str | None
    source_pack_id: str | None
    test_code: str
    test_type_code: str
    monitoring_frequency: str
    linked_asset_id: str | None
    connector_type_code: str | None
    connector_name: str | None
    policy_container_code: str | None
    policy_container_name: str | None
    version_number: int
    is_active: bool
    promoted_by: str
    promoted_at: str
    is_deleted: bool
    name: str | None
    description: str | None
    evaluation_rule: str | None
    signal_type: str | None
    integration_guide: str | None
    control_test_id: str | None
    created_at: str
    updated_at: str

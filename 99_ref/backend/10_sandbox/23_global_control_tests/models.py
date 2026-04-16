from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalControlTestRecord:
    id: str
    global_code: str
    connector_type_code: str
    connector_type_name: str | None
    version_number: int
    bundle: str  # JSON string
    source_signal_id: str | None
    source_policy_id: str | None
    source_library_id: str | None
    source_org_id: str | None
    linked_dataset_code: str | None
    publish_status: str
    is_featured: bool
    download_count: int
    signal_count: int
    published_by: str | None
    published_at: str | None
    is_active: bool
    is_deleted: bool
    created_at: str
    updated_at: str
    # Flattened EAV
    name: str | None
    description: str | None
    tags: str | None
    category: str | None
    changelog: str | None
    compliance_references: str | None


@dataclass(frozen=True)
class GlobalControlTestPullRecord:
    id: str
    global_test_id: str
    pulled_version: int
    target_org_id: str
    target_workspace_id: str | None
    deploy_type: str
    created_signal_ids: list[str] | None
    created_threat_id: str | None
    created_policy_id: str | None
    pulled_by: str
    pulled_at: str

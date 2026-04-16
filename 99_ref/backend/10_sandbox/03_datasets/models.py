from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetRecord:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None
    connector_instance_id: str | None
    dataset_code: str
    dataset_source_code: str
    version_number: int
    schema_fingerprint: str | None
    row_count: int
    byte_size: int
    collected_at: str | None
    is_locked: bool
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None
    description: str | None
    asset_ids: list[str] | None


@dataclass(frozen=True)
class DatasetDataRecord:
    id: str
    dataset_id: str
    record_seq: int
    record_name: str
    recorded_at: str
    source_asset_id: str | None
    connector_instance_id: str | None
    record_data: str  # JSON string
    description: str

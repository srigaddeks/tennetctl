from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalDatasetRecord:
    id: str
    global_code: str
    connector_type_code: str
    connector_type_name: str | None
    version_number: int
    json_schema: str  # JSON string
    sample_payload: str  # JSON string
    record_count: int
    publish_status: str
    is_featured: bool
    download_count: int
    source_dataset_id: str | None
    source_org_id: str | None
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
    collection_query: str | None
    compatible_asset_types: str | None
    changelog: str | None


@dataclass(frozen=True)
class GlobalDatasetPullRecord:
    id: str
    global_dataset_id: str
    pulled_version: int
    target_org_id: str
    target_workspace_id: str | None
    target_dataset_id: str | None
    pulled_by: str
    pulled_at: str

from __future__ import annotations

from pydantic import BaseModel, Field


class AssetResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None = None
    connector_instance_id: str
    provider_code: str
    asset_type_code: str
    asset_external_id: str
    parent_asset_id: str | None = None
    status_code: str
    current_snapshot_id: str | None = None
    last_collected_at: str | None = None
    consecutive_misses: int
    created_by: str
    created_at: str
    updated_at: str
    is_deleted: bool
    properties: dict[str, str] | None = None


class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    total: int


class AssetPropertyResponse(BaseModel):
    id: str
    asset_id: str
    property_key: str
    property_value: str
    value_type: str
    collected_at: str


class AssetSnapshotResponse(BaseModel):
    id: str
    asset_id: str
    collection_run_id: str | None = None
    snapshot_number: int
    schema_fingerprint: str
    property_count: int
    collected_at: str


class AssetChangeEntry(BaseModel):
    property_key: str
    old_value: str | None = None
    new_value: str | None = None
    changed_at: str


class AssetAccessGrantRequest(BaseModel):
    user_group_id: str = Field(..., min_length=1)
    role_code: str = Field(..., pattern=r"^(view|use|edit)$")


class AssetAccessGrantResponse(BaseModel):
    id: str
    asset_id: str
    user_group_id: str
    role_code: str
    granted_by: str
    granted_at: str


class AssetStatsByType(BaseModel):
    asset_type_code: str
    count: int


class AssetStatsByStatus(BaseModel):
    status_code: str
    count: int


class ConnectorHealthSummary(BaseModel):
    connector_id: str
    provider_code: str | None
    health_status: str
    consecutive_failures: int
    last_collected_at: str | None
    collection_schedule: str


class AssetStatsResponse(BaseModel):
    total_assets: int
    by_type: list[AssetStatsByType]
    by_status: list[AssetStatsByStatus]
    connectors: list[ConnectorHealthSummary]
    last_collection_at: str | None

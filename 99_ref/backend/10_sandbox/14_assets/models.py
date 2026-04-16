from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Asset:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None
    connector_instance_id: str
    provider_code: str
    asset_type_code: str
    asset_external_id: str
    parent_asset_id: str | None
    status_code: str
    current_snapshot_id: str | None
    last_collected_at: str | None
    consecutive_misses: int
    created_by: str
    created_at: str
    updated_at: str
    is_deleted: bool


@dataclass(frozen=True)
class AssetProperty:
    id: str
    asset_id: str
    property_key: str
    property_value: str
    value_type: str
    collected_at: str


@dataclass(frozen=True)
class AssetSnapshot:
    id: str
    asset_id: str
    collection_run_id: str | None
    snapshot_number: int
    schema_fingerprint: str
    property_count: int
    collected_at: str


@dataclass(frozen=True)
class AssetSnapshotProperty:
    id: str
    snapshot_id: str
    property_key: str
    property_value: str
    value_type: str


@dataclass(frozen=True)
class AssetAccessGrant:
    id: str
    asset_id: str
    user_group_id: str
    role_code: str
    granted_by: str
    granted_at: str

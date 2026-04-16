from __future__ import annotations

from pydantic import BaseModel, Field


class CreateDatasetRequest(BaseModel):
    dataset_source_code: str = Field(..., min_length=1, max_length=50)
    workspace_id: str | None = None
    connector_instance_id: str | None = None
    asset_ids: list[str] | None = None
    properties: dict[str, str] | None = None
    # Initial records to add on creation — each item is an individual JSON object
    records: list[dict] | None = None


class AddRecordsRequest(BaseModel):
    records: list[dict] = Field(..., min_length=1)
    source_asset_id: str | None = None
    connector_instance_id: str | None = None


class UpdateDatasetRequest(BaseModel):
    properties: dict[str, str] | None = None
    asset_ids: list[str] | None = None
    connector_instance_id: str | None = None


class FieldOverrideRequest(BaseModel):
    field_path: str = Field(..., min_length=1, max_length=500)
    override_source: str = Field(..., min_length=1, max_length=100)
    override_value: str | None = None


class DatasetResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None = None
    connector_instance_id: str | None = None
    dataset_code: str
    dataset_source_code: str
    version_number: int
    schema_fingerprint: str | None = None
    row_count: int = 0
    byte_size: int = 0
    collected_at: str | None = None
    is_locked: bool = False
    is_active: bool = True
    created_at: str
    updated_at: str
    name: str | None = None
    description: str | None = None
    asset_ids: list[str] | None = None


class DatasetListResponse(BaseModel):
    items: list[DatasetResponse]
    total: int


class DatasetDataRecord(BaseModel):
    id: str
    dataset_id: str
    record_seq: int
    record_name: str = ""
    recorded_at: str
    source_asset_id: str | None = None
    connector_instance_id: str | None = None
    record_data: dict
    description: str = ""


class UpdateRecordDescriptionRequest(BaseModel):
    description: str = Field(..., max_length=10000)


class UpdateRecordNameRequest(BaseModel):
    record_name: str = Field(..., min_length=1, max_length=120, pattern=r"^[a-z0-9][a-z0-9_\-]{0,118}[a-z0-9]?$")


class DatasetRecordsResponse(BaseModel):
    dataset_id: str
    records: list[DatasetDataRecord]
    total: int


# ── Dataset composition ────────────────────────────────────────────────────────

class DatasetSourceRef(BaseModel):
    """Reference to a source of asset properties for dataset composition."""
    source_type: str = Field(..., description="asset_properties | asset_snapshot")
    connector_instance_id: str | None = Field(None, description="Filter by connector instance")
    asset_type_filter: str | None = Field(None, description="Filter by asset type code (e.g. 'postgres_role')")
    asset_id: str | None = Field(None, description="Filter by specific asset ID")
    snapshot_id: str | None = Field(None, description="For asset_snapshot: specific snapshot UUID")
    limit: int | None = Field(None, description="Max records per source (smart sampling)", ge=1, le=1000)


class ComposeDatasetRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    workspace_id: str | None = None
    sources: list[DatasetSourceRef] = Field(..., min_length=1)


class ComposeDatasetResponse(BaseModel):
    dataset_id: str
    dataset_code: str
    version_number: int
    dataset_source_code: str
    schema_fingerprint: str | None = None
    row_count: int
    record_preview: dict


# ── Schema drift ───────────────────────────────────────────────────────────────

class FieldChange(BaseModel):
    path: str
    type: str | None = None
    was: str | None = None
    now: str | None = None


class SchemaDriftResponse(BaseModel):
    dataset_id: str
    has_drift: bool
    original_fingerprint: str | None = None
    current_fingerprint: str | None = None
    changes: dict  # {added_fields, removed_fields, type_changes}
    recommendation: str


# ── Asset type discovery + sample preview ─────────────────────────────────────

class UpdateRecordRequest(BaseModel):
    record_data: dict


class CreateVersionRequest(BaseModel):
    """Snapshot current records as a new immutable version."""
    description: str | None = None


class DatasetVersionResponse(BaseModel):
    version_number: int
    record_count: int
    schema_fingerprint: str | None = None
    created_at: str
    description: str | None = None
    is_current: bool = False


class DatasetVersionListResponse(BaseModel):
    dataset_code: str
    versions: list[DatasetVersionResponse]


class AssetTypeInfo(BaseModel):
    asset_type_code: str
    asset_count: int
    sample_property_keys: list[str] = Field(default_factory=list)


class ConnectorAssetTypesResponse(BaseModel):
    connector_instance_id: str
    connector_name: str | None = None
    provider_code: str | None = None
    asset_types: list[AssetTypeInfo]


class AssetSampleRecord(BaseModel):
    asset_id: str
    asset_external_id: str | None = None
    properties: dict


class AssetSamplesResponse(BaseModel):
    connector_instance_id: str
    asset_type_code: str
    total_count: int
    property_keys: list[str]
    samples: list[AssetSampleRecord]


# ── Smart dataset composition ─────────────────────────────────────────────────

class SmartComposeRequest(BaseModel):
    connector_instance_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    workspace_id: str | None = None
    samples_per_type: int = Field(default=10, ge=1, le=100)

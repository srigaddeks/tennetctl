from __future__ import annotations

from pydantic import BaseModel, Field


# ── Request models ────────────────────────────────────────────────────────────

class PublishGlobalDatasetRequest(BaseModel):
    source_dataset_id: str = Field(..., description="UUID of the sandbox dataset to publish")
    global_code: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    properties: dict[str, str] = Field(default_factory=dict)


class UpdateGlobalDatasetRequest(BaseModel):
    properties: dict[str, str] | None = None
    is_featured: bool | None = None


class PullGlobalDatasetRequest(BaseModel):
    org_id: str
    workspace_id: str | None = None
    connector_instance_id: str | None = None
    custom_dataset_code: str | None = None


# ── Response models ───────────────────────────────────────────────────────────

class GlobalDatasetResponse(BaseModel):
    id: str
    global_code: str
    connector_type_code: str
    connector_type_name: str | None = None
    version_number: int
    json_schema: dict = Field(default_factory=dict)
    sample_payload: list = Field(default_factory=list)
    record_count: int = 0
    publish_status: str = "published"
    is_featured: bool = False
    download_count: int = 0
    source_dataset_id: str | None = None
    source_org_id: str | None = None
    published_by: str | None = None
    published_at: str | None = None
    created_at: str = ""
    updated_at: str = ""
    # Flattened EAV
    name: str | None = None
    description: str | None = None
    tags: str | None = None
    category: str | None = None
    collection_query: str | None = None
    compatible_asset_types: str | None = None
    changelog: str | None = None


class GlobalDatasetListResponse(BaseModel):
    items: list[GlobalDatasetResponse]
    total: int


class GlobalDatasetVersionResponse(BaseModel):
    version_number: int
    publish_status: str
    record_count: int
    published_at: str | None = None
    changelog: str | None = None
    created_at: str = ""


class GlobalDatasetVersionListResponse(BaseModel):
    global_code: str
    versions: list[GlobalDatasetVersionResponse]


class GlobalDatasetStatsResponse(BaseModel):
    total: int
    by_connector_type: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    featured_count: int = 0


class PullResultResponse(BaseModel):
    local_dataset_id: str
    dataset_code: str
    version_number: int
    global_source_code: str
    global_source_version: int

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateConnectorRequest(BaseModel):
    instance_code: str = Field(
        ..., min_length=3, max_length=100, pattern=r"^[a-z0-9][a-z0-9\-]{1,98}[a-z0-9]$"
    )
    connector_type_code: str = Field(..., min_length=1, max_length=50)
    workspace_id: str | None = None
    asset_version_id: str | None = None
    collection_schedule: str = Field(default="manual", max_length=100)
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    properties: dict[str, str] | None = None
    credentials: dict[str, str] | None = None
    is_draft: bool = False


class UpdateConnectorRequest(BaseModel):
    collection_schedule: str | None = Field(None, max_length=100)
    asset_version_id: str | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    properties: dict[str, str] | None = None
    is_active: bool | None = None


class PreflightTestRequest(BaseModel):
    connector_type_code: str = Field(..., min_length=1, max_length=50)
    credentials: dict[str, str] = Field(default_factory=dict)
    properties: dict[str, str] = Field(default_factory=dict)


class UpdateCredentialsRequest(BaseModel):
    credentials: dict[str, str] = Field(..., min_length=1)


class ConnectorResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None = None
    instance_code: str
    connector_type_code: str
    connector_type_name: str | None = None
    connector_category_code: str | None = None
    connector_category_name: str | None = None
    asset_version_id: str | None = None
    collection_schedule: str
    last_collected_at: str | None = None
    health_status: str
    is_active: bool
    is_draft: bool = False
    created_at: str
    updated_at: str
    name: str | None = None
    description: str | None = None


class ConnectorListResponse(BaseModel):
    items: list[ConnectorResponse]
    total: int


class TestConnectionResponse(BaseModel):
    health_status: str
    message: str
    tested_at: str


class CollectResponse(BaseModel):
    dataset_id: str
    dataset_code: str
    version_number: int
    collected_at: str

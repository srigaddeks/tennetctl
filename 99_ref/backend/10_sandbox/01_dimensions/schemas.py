from __future__ import annotations

from pydantic import BaseModel


class SandboxDimensionResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool


class SandboxDimensionListResponse(BaseModel):
    items: list[SandboxDimensionResponse]
    count: int


class AssetVersionResponse(BaseModel):
    id: str
    connector_type_code: str
    version_code: str
    version_label: str
    is_latest: bool
    is_active: bool
    sort_order: int


class ConnectorConfigField(BaseModel):
    key: str
    label: str
    type: str  # text | password | textarea | select | boolean | number
    required: bool
    credential: bool  # True → stored encrypted; False → stored as property
    placeholder: str | None = None
    hint: str | None = None
    options: list[str] | None = None  # for type=select
    validation: str | None = None  # regex string
    order: int = 0


class ConnectorConfigSchemaResponse(BaseModel):
    connector_type_code: str
    fields: list[ConnectorConfigField]
    supports_steampipe: bool
    steampipe_plugin: str | None

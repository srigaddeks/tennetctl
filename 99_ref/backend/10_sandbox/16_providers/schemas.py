from __future__ import annotations

from pydantic import BaseModel


class ProviderConfigSchemaFieldSchema(BaseModel):
    key: str
    label: str
    type: str
    required: bool
    credential: bool
    placeholder: str | None = None
    hint: str | None = None
    validation: str | None = None
    default: str | None = None
    order: int


class ProviderDefinitionSchema(BaseModel):
    id: str
    code: str
    name: str
    driver_module: str
    default_auth_method: str
    supports_log_collection: bool
    supports_steampipe: bool
    supports_custom_driver: bool
    steampipe_plugin: str | None = None
    rate_limit_rpm: int
    is_active: bool
    is_coming_soon: bool
    created_at: str
    updated_at: str
    config_fields: list[ProviderConfigSchemaFieldSchema]


class ProviderListResponse(BaseModel):
    items: list[ProviderDefinitionSchema]
    total: int


class ProviderVersionSchema(BaseModel):
    id: str
    provider_code: str
    version_code: str
    name: str
    config_schema_override: dict | None = None
    is_active: bool
    is_default: bool
    created_at: str

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


_VALID_SCHEDULES = {"hourly", "daily", "weekly", "manual"}


class CreateAssetConnectorRequest(BaseModel):
    """Create a new asset inventory connector."""
    provider_code: str = Field(..., description="Provider definition code (e.g. 'github', 'azure_storage')")
    provider_version_code: str | None = Field(None, description="Pin to a specific provider version (e.g. '2022-11-28'). NULL = use provider default.")
    connection_config: dict[str, Any] = Field(default_factory=dict, description="Non-credential connection config matching the provider config_schema")
    credentials: dict[str, str] = Field(default_factory=dict, description="Credential fields (marked credential:true in schema). Encrypted at rest.")
    collection_schedule: str = Field("daily", description="hourly | daily | weekly | manual")
    name: str | None = Field(None, max_length=200)
    description: str | None = Field(None)

    @field_validator("collection_schedule")
    @classmethod
    def validate_schedule(cls, v: str) -> str:
        if v not in _VALID_SCHEDULES:
            raise ValueError(f"collection_schedule must be one of: {', '.join(sorted(_VALID_SCHEDULES))}")
        return v


class UpdateAssetConnectorRequest(BaseModel):
    """Update schedule, config, or credentials on an existing asset connector."""
    connection_config: dict[str, Any] | None = Field(None)
    credentials: dict[str, str] | None = Field(None, description="If provided, replaces all existing credentials")
    collection_schedule: str | None = Field(None)
    provider_version_code: str | None = Field(None)
    name: str | None = Field(None, max_length=200)
    description: str | None = Field(None)
    is_active: bool | None = Field(None)

    @field_validator("collection_schedule")
    @classmethod
    def validate_schedule(cls, v: str | None) -> str | None:
        if v is not None and v not in _VALID_SCHEDULES:
            raise ValueError(f"collection_schedule must be one of: {', '.join(sorted(_VALID_SCHEDULES))}")
        return v


class AssetConnectorResponse(BaseModel):
    id: str
    org_id: str
    provider_code: str | None
    provider_version_code: str | None
    connection_config: dict[str, Any] | None   # Non-credential fields only — never returns credentials
    collection_schedule: str
    last_collected_at: str | None
    health_status: str
    consecutive_failures: int
    cooldown_until: str | None
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None
    description: str | None

    model_config = {"from_attributes": True}


class AssetConnectorListResponse(BaseModel):
    items: list[AssetConnectorResponse]
    total: int


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    latency_ms: int | None = None

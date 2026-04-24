"""Pydantic v2 schemas for geography.service_zones."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ZoneStatus = Literal["active", "paused"]


class ServiceZoneCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kitchen_id: str
    name: str = Field(min_length=1, max_length=200)
    polygon_jsonb: dict[str, Any] = Field(default_factory=dict)
    status: ZoneStatus = "active"
    properties: dict[str, Any] = Field(default_factory=dict)


class ServiceZoneUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kitchen_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    polygon_jsonb: dict[str, Any] | None = None
    status: ZoneStatus | None = None
    properties: dict[str, Any] | None = None


class ServiceZoneOut(BaseModel):
    """Mirror of v_service_zones row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    kitchen_id: str
    kitchen_name: str | None = None
    name: str
    polygon_jsonb: dict[str, Any] = Field(default_factory=dict)
    status: ZoneStatus
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


class ServiceZoneListFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kitchen_id: str | None = None
    status: ZoneStatus | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    include_deleted: bool = False

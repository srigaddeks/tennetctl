"""Pydantic v2 schemas for geography.locations + regions (read-only)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RegionOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    country_code: str
    state_name: str
    regulatory_body: str | None = None
    default_currency_code: str
    default_timezone: str
    deprecated_at: datetime | None = None


class LocationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    region_id: int
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    timezone: str = Field(min_length=1, max_length=100)
    properties: dict[str, Any] = Field(default_factory=dict)


class LocationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    region_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    timezone: str | None = Field(default=None, min_length=1, max_length=100)
    properties: dict[str, Any] | None = None


class LocationOut(BaseModel):
    """Mirror of v_locations row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    region_id: int
    region_code: str | None = None
    country_code: str | None = None
    regulatory_body: str | None = None
    default_currency_code: str | None = None
    default_timezone: str | None = None
    name: str
    slug: str
    timezone: str
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


class LocationListFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    region_id: int | None = None
    q: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    include_deleted: bool = False

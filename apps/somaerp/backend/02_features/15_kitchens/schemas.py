"""Pydantic v2 schemas for geography.kitchens."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

KitchenType = Literal["home", "commissary", "satellite"]
KitchenStatus = Literal["active", "paused", "decommissioned"]


class KitchenCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location_id: str
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    kitchen_type: KitchenType
    address_jsonb: dict[str, Any] = Field(default_factory=dict)
    geo_lat: Decimal | None = None
    geo_lng: Decimal | None = None
    status: KitchenStatus = "active"
    properties: dict[str, Any] = Field(default_factory=dict)


class KitchenUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    kitchen_type: KitchenType | None = None
    address_jsonb: dict[str, Any] | None = None
    geo_lat: Decimal | None = None
    geo_lng: Decimal | None = None
    status: KitchenStatus | None = None
    properties: dict[str, Any] | None = None


class KitchenOut(BaseModel):
    """Mirror of v_kitchens row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    location_id: str
    location_name: str | None = None
    location_slug: str | None = None
    region_code: str | None = None
    currency: str | None = None
    tz: str | None = None
    name: str
    slug: str
    kitchen_type: KitchenType
    address_jsonb: dict[str, Any] = Field(default_factory=dict)
    geo_lat: Decimal | None = None
    geo_lng: Decimal | None = None
    status: KitchenStatus
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


class KitchenListFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location_id: str | None = None
    status: KitchenStatus | None = None
    q: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    include_deleted: bool = False

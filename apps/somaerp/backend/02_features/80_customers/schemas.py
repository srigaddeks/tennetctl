"""Pydantic v2 schemas for customers."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CustomerStatus = Literal["prospect", "active", "paused", "churned", "blocked"]


class CustomerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location_id: str | None = None
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    email: str | None = None
    phone: str | None = None
    address_jsonb: dict[str, Any] = Field(default_factory=dict)
    delivery_notes: str | None = None
    acquisition_source: str | None = None
    status: CustomerStatus = "active"
    properties: dict[str, Any] = Field(default_factory=dict)


class CustomerUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    location_id: str | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    email: str | None = None
    phone: str | None = None
    address_jsonb: dict[str, Any] | None = None
    delivery_notes: str | None = None
    acquisition_source: str | None = None
    status: CustomerStatus | None = None
    properties: dict[str, Any] | None = None
    somacrm_contact_id: str | None = None


class CustomerOut(BaseModel):
    """Mirror of v_customers row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    location_id: str | None = None
    location_name: str | None = None
    name: str
    slug: str
    email: str | None = None
    phone: str | None = None
    address_jsonb: dict[str, Any] = Field(default_factory=dict)
    delivery_notes: str | None = None
    acquisition_source: str | None = None
    status: CustomerStatus
    lifetime_value: Decimal
    somacrm_contact_id: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    active_subscription_count: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None

"""Pydantic v2 schemas for organizations."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrgCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=500)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    industry: str | None = Field(default=None, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=500)
    employee_count: int | None = None
    annual_revenue: Decimal | None = None
    description: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class OrgUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=500)
    slug: str | None = Field(default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    industry: str | None = Field(default=None, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=500)
    employee_count: int | None = None
    annual_revenue: Decimal | None = None
    description: str | None = None
    properties: dict[str, Any] | None = None


class OrgOut(BaseModel):
    """Mirror of v_organizations row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    name: str
    slug: str
    industry: str | None = None
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    employee_count: int | None = None
    annual_revenue: Decimal | None = None
    description: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    contact_count: int = 0
    deal_count: int = 0
    deleted_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: datetime
    updated_at: datetime

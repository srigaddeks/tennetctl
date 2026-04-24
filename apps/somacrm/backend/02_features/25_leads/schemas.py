"""Pydantic v2 schemas for leads."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LeadCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=500)
    contact_id: str | None = None
    organization_id: str | None = None
    first_name: str | None = Field(default=None, max_length=200)
    last_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=100)
    company: str | None = Field(default=None, max_length=200)
    lead_source: str | None = Field(default=None, max_length=200)
    status_id: int = Field(default=1)
    score: int = Field(default=0, ge=0, le=100)
    assigned_to: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class LeadUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=500)
    contact_id: str | None = None
    organization_id: str | None = None
    first_name: str | None = Field(default=None, max_length=200)
    last_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=100)
    company: str | None = Field(default=None, max_length=200)
    lead_source: str | None = Field(default=None, max_length=200)
    status_id: int | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    assigned_to: str | None = None
    converted_deal_id: str | None = None
    converted_at: datetime | None = None
    properties: dict[str, Any] | None = None


class LeadOut(BaseModel):
    """Mirror of v_leads row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    title: str
    contact_id: str | None = None
    organization_id: str | None = None
    contact_name: str | None = None
    organization_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    lead_source: str | None = None
    status_id: int
    status: str | None = None
    score: int = 0
    assigned_to: str | None = None
    converted_deal_id: str | None = None
    converted_at: datetime | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    deleted_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: datetime
    updated_at: datetime

"""Pydantic v2 schemas for contacts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ContactCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    first_name: str = Field(min_length=1, max_length=200)
    last_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=100)
    mobile: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=200)
    company_name: str | None = Field(default=None, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    linkedin_url: str | None = Field(default=None, max_length=500)
    twitter_handle: str | None = Field(default=None, max_length=200)
    lead_source: str | None = Field(default=None, max_length=200)
    organization_id: str | None = None
    status_id: int = Field(default=1)
    properties: dict[str, Any] = Field(default_factory=dict)


class ContactUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    first_name: str | None = Field(default=None, min_length=1, max_length=200)
    last_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=100)
    mobile: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=200)
    company_name: str | None = Field(default=None, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    linkedin_url: str | None = Field(default=None, max_length=500)
    twitter_handle: str | None = Field(default=None, max_length=200)
    lead_source: str | None = Field(default=None, max_length=200)
    organization_id: str | None = None
    status_id: int | None = None
    properties: dict[str, Any] | None = None


class ContactOut(BaseModel):
    """Mirror of v_contacts row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    organization_id: str | None = None
    organization_name: str | None = None
    first_name: str
    last_name: str | None = None
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    job_title: str | None = None
    company_name: str | None = None
    website: str | None = None
    linkedin_url: str | None = None
    twitter_handle: str | None = None
    lead_source: str | None = None
    status_id: int
    status: str | None = None
    notes_count: int = 0
    activities_count: int = 0
    deals_count: int = 0
    properties: dict[str, Any] = Field(default_factory=dict)
    deleted_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: datetime
    updated_at: datetime

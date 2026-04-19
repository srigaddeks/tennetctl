"""Pydantic schemas for product_ops.links."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SLUG_RE = re.compile(r"^[a-zA-Z0-9_-]{2,64}$")


class CreateShortLinkBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str | None = Field(default=None, max_length=64)
    target_url: str = Field(min_length=1, max_length=2048)
    workspace_id: str | None = None
    utm_source: str | None = Field(default=None, max_length=256)
    utm_medium: str | None = Field(default=None, max_length=256)
    utm_campaign: str | None = Field(default=None, max_length=256)
    utm_term: str | None = Field(default=None, max_length=256)
    utm_content: str | None = Field(default=None, max_length=256)

    @field_validator("slug")
    @classmethod
    def _slug_shape(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not _SLUG_RE.match(v):
            raise ValueError("slug must match [A-Za-z0-9_-]{2,64}")
        return v


class UpdateShortLinkBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_url: str | None = Field(default=None, max_length=2048)
    is_active: bool | None = None
    utm_source: str | None = Field(default=None, max_length=256)
    utm_medium: str | None = Field(default=None, max_length=256)
    utm_campaign: str | None = Field(default=None, max_length=256)
    utm_term: str | None = Field(default=None, max_length=256)
    utm_content: str | None = Field(default=None, max_length=256)
    deleted_at: datetime | None = None  # operator can soft-delete via PATCH


class ShortLinkOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    slug: str
    target_url: str
    org_id: str
    workspace_id: str
    utm_source: str | None
    utm_medium: str | None
    utm_campaign: str | None
    utm_term: str | None
    utm_content: str | None
    is_active: bool
    is_deleted: bool
    deleted_at: datetime | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class ShortLinkListResponse(BaseModel):
    items: list[ShortLinkOut]
    total: int

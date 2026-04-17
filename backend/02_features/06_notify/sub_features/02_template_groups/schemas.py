"""Pydantic schemas for notify.template_groups."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TemplateGroupCreate(BaseModel):
    org_id: str
    key: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    label: str = Field(..., min_length=1, max_length=128)
    category_id: int = Field(..., ge=1, le=4, description="1=transactional, 2=critical, 3=marketing, 4=digest")
    smtp_config_id: str | None = None


class TemplateGroupUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=128)
    category_id: int | None = Field(default=None, ge=1, le=4)
    smtp_config_id: str | None = None
    is_active: bool | None = None


class TemplateGroupRow(BaseModel):
    id: str
    org_id: str
    key: str
    label: str
    category_id: int
    category_code: str
    category_label: str
    smtp_config_id: str | None
    smtp_config_key: str | None
    is_active: bool
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime

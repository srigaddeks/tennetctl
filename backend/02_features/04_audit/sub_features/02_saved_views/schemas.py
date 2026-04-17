"""Pydantic schemas for audit saved views sub-feature."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditSavedViewCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    filter_json: dict[str, Any] = Field(default_factory=dict)
    bucket: str = Field(default="hour", pattern="^(hour|day)$")


class AuditSavedViewRow(BaseModel):
    id: str
    org_id: str
    user_id: str | None
    name: str
    filter_json: dict[str, Any]
    bucket: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditSavedViewListResponse(BaseModel):
    items: list[AuditSavedViewRow]
    total: int

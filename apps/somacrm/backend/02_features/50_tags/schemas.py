"""Pydantic v2 schemas for tags and entity-tags."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TagCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#6366f1", max_length=20)


class TagUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, max_length=20)


class TagOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    name: str
    color: str
    deleted_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: datetime
    updated_at: datetime


class EntityTagCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entity_type: Literal["contact", "organization", "lead", "deal"]
    entity_id: str
    tag_id: str


class EntityTagOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    entity_type: str
    entity_id: str
    tag_id: str
    created_by: str | None = None
    created_at: datetime

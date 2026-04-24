"""Pydantic v2 schemas for notes."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entity_type: Literal["contact", "organization", "lead", "deal"]
    entity_id: str
    content: str = Field(min_length=1)
    is_pinned: bool = False
    properties: dict[str, Any] = Field(default_factory=dict)


class NoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str | None = Field(default=None, min_length=1)
    is_pinned: bool | None = None
    properties: dict[str, Any] | None = None


class NoteOut(BaseModel):
    """Mirror of v_notes row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    entity_type: str
    entity_id: str
    content: str
    is_pinned: bool
    properties: dict[str, Any] = Field(default_factory=dict)
    deleted_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: datetime
    updated_at: datetime

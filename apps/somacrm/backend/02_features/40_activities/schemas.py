"""Pydantic v2 schemas for activities."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ActivityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    activity_type_id: int
    title: str = Field(min_length=1, max_length=500)
    status_id: int = Field(default=1)
    description: str | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None
    duration_minutes: int | None = None
    entity_type: Literal["contact", "organization", "lead", "deal"] | None = None
    entity_id: str | None = None
    assigned_to: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class ActivityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    activity_type_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=500)
    status_id: int | None = None
    description: str | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None
    duration_minutes: int | None = None
    entity_type: Literal["contact", "organization", "lead", "deal"] | None = None
    entity_id: str | None = None
    assigned_to: str | None = None
    properties: dict[str, Any] | None = None


class ActivityOut(BaseModel):
    """Mirror of v_activities row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    activity_type_id: int
    activity_type: str | None = None
    activity_type_label: str | None = None
    activity_type_icon: str | None = None
    status_id: int
    status: str | None = None
    title: str
    description: str | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None
    duration_minutes: int | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    assigned_to: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    deleted_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: datetime
    updated_at: datetime

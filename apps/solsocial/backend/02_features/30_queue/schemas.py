"""Pydantic schemas for queues."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SlotIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    day_of_week: int = Field(ge=0, le=6)
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)


class SlotOut(SlotIn):
    id: str
    queue_id: str
    created_at: datetime


class QueueOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    channel_id: str
    workspace_id: str
    org_id: str
    timezone: str
    created_at: datetime
    updated_at: datetime
    slots: list[SlotOut] = Field(default_factory=list)


class QueueUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel_id: str
    timezone: str = "UTC"
    slots: list[SlotIn] = Field(default_factory=list)

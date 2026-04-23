"""Pydantic v2 schemas for channels."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Provider = Literal["linkedin", "twitter", "instagram"]


class ChannelOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    org_id: str
    workspace_id: str
    provider_code: Provider
    handle: str
    display_name: str | None = None
    avatar_url: str | None = None
    external_id: str | None = None
    connected_at: datetime
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ChannelPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str | None = Field(default=None, max_length=200)
    avatar_url: str | None = Field(default=None, max_length=500)

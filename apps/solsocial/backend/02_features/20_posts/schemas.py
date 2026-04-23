"""Pydantic v2 schemas for posts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

PostStatus = Literal["draft", "queued", "scheduled", "publishing", "published", "failed"]


class MediaItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["image", "video"]
    url: str
    alt: str | None = None


class PostCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    channel_id: str
    body: str = Field(min_length=1, max_length=10000)
    media: list[MediaItem] = Field(default_factory=list)
    link: str | None = None
    status: PostStatus = "draft"
    scheduled_at: datetime | None = None


class PostPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: str | None = Field(default=None, max_length=10000)
    media: list[MediaItem] | None = None
    link: str | None = None
    status: PostStatus | None = None
    scheduled_at: datetime | None = None


class PostOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    org_id: str
    workspace_id: str
    channel_id: str
    status: PostStatus
    body: str
    media: list[dict[str, Any]] = Field(default_factory=list)
    link: str | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    external_post_id: str | None = None
    external_url: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime

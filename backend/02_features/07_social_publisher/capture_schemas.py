"""social_publisher.capture — Pydantic schemas for ingest + list."""
from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, Field

Platform = Literal["linkedin", "x", "twitter"]
CaptureType = Literal[
    "feed_post_seen",
    "own_post_published",
    "comment_seen",
    "own_comment",
    "profile_viewed",
]

_PLATFORM_ALIASES: dict[str, str] = {"twitter": "x"}


def normalise_platform(p: str) -> str:
    return _PLATFORM_ALIASES.get(p, p)


class CaptureIn(BaseModel):
    platform: Platform
    type: CaptureType
    platform_post_id: str = Field(min_length=1, max_length=512)
    observed_at: dt.datetime
    extractor_version: str = Field(default="v1", max_length=32)
    author_handle: str | None = None
    author_name: str | None = None
    text_excerpt: str | None = None
    url: str | None = None
    like_count: int | None = None
    reply_count: int | None = None
    repost_count: int | None = None
    view_count: int | None = None
    is_own: bool = False
    raw_attrs: dict[str, Any] = Field(default_factory=dict)


class CaptureBatchIn(BaseModel):
    captures: list[CaptureIn] = Field(min_length=1, max_length=100)


class CaptureOut(BaseModel):
    id: str
    platform: str
    type: str
    platform_post_id: str
    observed_at: dt.datetime
    author_handle: str | None
    author_name: str | None
    text_excerpt: str | None
    url: str | None
    like_count: int | None
    reply_count: int | None
    repost_count: int | None
    view_count: int | None
    is_own: bool
    extractor_version: str
    created_at: dt.datetime


class CaptureBatchOut(BaseModel):
    inserted: int
    deduped: int
    ids: list[str]


class CaptureListOut(BaseModel):
    items: list[CaptureOut]
    total: int
    limit: int
    offset: int

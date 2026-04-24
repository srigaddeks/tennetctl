"""social_publisher.capture — Pydantic schemas for ingest + list + insights."""
from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, Field, field_serializer

Platform = Literal["linkedin", "x", "twitter"]


def _to_utc_iso(v: dt.datetime | None) -> str | None:
    """Serialize a naive-UTC datetime as an explicit Z-suffixed ISO string."""
    if v is None:
        return None
    if v.tzinfo is None:
        v = v.replace(tzinfo=dt.timezone.utc)
    return v.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


CaptureType = Literal[
    # Core (v1 — still accepted; own_* are normalized to base + is_own=True)
    "feed_post_seen",
    "own_post_published",
    "comment_seen",
    "own_comment",
    "profile_viewed",
    # Expanded (v2) — LinkedIn
    "article_seen",
    "article_opened",
    "newsletter_seen",
    "company_viewed",
    "profile_page_viewed",
    "job_post_seen",
    "job_post_opened",
    "poll_seen",
    "event_seen",
    "hashtag_feed_seen",
    "search_result_seen",
    "reshare_seen",
    "reaction_detail",
    "connection_suggested",
    "notification_seen",
    "live_broadcast_seen",
    # Expanded (v2) — Twitter/X
    "quote_tweet_seen",
    "thread_seen",
    "list_viewed",
    "space_seen",
    "community_seen",
    # Behavior signals (v3) — interaction events, not content
    "post_dwell",
    "post_clicked",
    "text_selected",
    "text_copied",
    "video_played",
    "link_hovered",
    "page_visit",
    # Deeper LinkedIn/Twitter coverage (v3)
    "job_recommendation",
    "messaging_thread",
    "activity_item",
    "saved_item",
    "reactors_list",
    "reposters_list",
    "follower_item",
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
    raw_attrs: dict[str, Any] = Field(default_factory=dict)
    workspace_id: str | None = None

    @field_serializer("observed_at", "created_at")
    def _serialize_utc(self, v: dt.datetime) -> str:
        return _to_utc_iso(v)  # type: ignore[return-value]


class CaptureBatchOut(BaseModel):
    inserted: int
    deduped: int
    metric_observations: int = 0
    rejected_empty: int = 0
    ids: list[str]


class CaptureListOut(BaseModel):
    items: list[CaptureOut]
    total: int
    limit: int
    offset: int


class MetricObservation(BaseModel):
    observed_at: dt.datetime
    like_count: int | None = None
    reply_count: int | None = None
    repost_count: int | None = None
    view_count: int | None = None
    reactions: dict[str, Any] | None = None

    @field_serializer("observed_at")
    def _serialize_utc(self, v: dt.datetime) -> str:
        return _to_utc_iso(v)  # type: ignore[return-value]


class MetricHistoryOut(BaseModel):
    capture_id: str
    observations: list[MetricObservation]


class TopAuthorRow(BaseModel):
    platform: str
    handle: str
    display_name: str | None
    capture_count: int
    total_likes_seen: int | None = None
    total_replies_seen: int | None = None
    first_seen_at: dt.datetime | None = None
    last_seen_at: dt.datetime | None = None

    @field_serializer("first_seen_at", "last_seen_at")
    def _serialize_utc(self, v: dt.datetime | None) -> str | None:
        return _to_utc_iso(v)


class TopHashtagRow(BaseModel):
    tag: str
    n: int


class PlatformCount(BaseModel):
    platform: str
    n: int


class TypeCount(BaseModel):
    type: str
    n: int


class CaptureCountsOut(BaseModel):
    total: int
    own_count: int
    today_count: int
    week_count: int
    by_platform: list[PlatformCount]
    by_type: list[TypeCount]

"""
product_ops.events — Pydantic v2 schemas for ingest + read.

The browser SDK posts batches to POST /v1/track. The payload uses domain-standard
"properties" (industry term — Mixpanel, PostHog, Plausible all use it). Server
stores it in the JSONB column named `metadata` (project DB convention). The
boundary translation lives in service.ingest_batch.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ── Ingest (write) ──────────────────────────────────────────────────

EventKind = Literal["page_view", "custom", "click", "identify", "alias", "referral_attached"]

# Map kind code → dim_event_kinds.id (statically seeded; safe to inline).
EVENT_KIND_ID: dict[str, int] = {
    "page_view": 1,
    "custom": 2,
    "click": 3,
    "identify": 4,
    "alias": 5,
    "referral_attached": 6,
}


class IngestEventIn(BaseModel):
    """One event in an inbound batch."""
    model_config = ConfigDict(extra="forbid")

    kind: EventKind
    anonymous_id: str = Field(min_length=1, max_length=128)
    occurred_at: datetime
    event_name: str | None = Field(default=None, max_length=128)
    page_url: str | None = Field(default=None, max_length=2048)
    referrer: str | None = Field(default=None, max_length=2048)
    properties: dict[str, Any] = Field(default_factory=dict)

    # UTM fields are extracted from page_url query string at ingest, but the
    # SDK can also pass them explicitly (e.g. for backend-emitted events).
    utm_source: str | None = Field(default=None, max_length=256)
    utm_medium: str | None = Field(default=None, max_length=256)
    utm_campaign: str | None = Field(default=None, max_length=256)
    utm_term: str | None = Field(default=None, max_length=256)
    utm_content: str | None = Field(default=None, max_length=256)

    @model_validator(mode="after")
    def _custom_requires_event_name(self) -> "IngestEventIn":
        if self.kind == "custom" and not self.event_name:
            raise ValueError("event_name is required when kind='custom'")
        return self

    @field_validator("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content")
    @classmethod
    def _utm_length_cap(cls, v: str | None) -> str | None:
        # Pydantic max_length on the field already enforces this; explicit
        # validator is here so the error code is precise (PRODUCT_OPS.UTM_TOO_LONG)
        # rather than a generic Pydantic length error. Service layer raises that
        # error code on ValueError.
        if v is not None and len(v) > 256:
            raise ValueError("utm value exceeds 256 characters")
        return v


class TrackBatchIn(BaseModel):
    """Inbound POST /v1/track payload."""
    model_config = ConfigDict(extra="forbid")

    project_key: str = Field(min_length=1, max_length=256)
    events: list[IngestEventIn] = Field(min_length=1, max_length=1000)
    dnt: bool = False  # mirrors browser DNT header; SDK reads it before sending


class TrackBatchResponse(BaseModel):
    accepted: int
    dropped_dnt: int = 0
    dropped_capped: int = 0


# ── Read ──────────────────────────────────────────────────────────────

class ProductEventOut(BaseModel):
    """Read shape from v_product_events."""
    model_config = ConfigDict(extra="ignore")

    id: str
    visitor_id: str
    user_id: str | None
    session_id: str | None
    org_id: str
    workspace_id: str
    event_kind: str
    event_name: str | None
    occurred_at: datetime
    page_url: str | None
    referrer: str | None
    metadata: dict[str, Any]
    created_at: datetime


class ProductEventListResponse(BaseModel):
    events: list[ProductEventOut]
    cursor: str | None = None


# ── Attribution resolve ──────────────────────────────────────────────

class AttributionTouch(BaseModel):
    occurred_at: datetime | None
    utm_source: str | None
    utm_medium: str | None
    utm_campaign: str | None
    utm_term: str | None
    utm_content: str | None
    referrer: str | None
    landing_url: str | None


class AttributionResolveOut(BaseModel):
    visitor_id: str
    first_touch: AttributionTouch | None
    last_touch: AttributionTouch | None

"""
audit.events — Pydantic v2 API models.

Shapes the read-path surface: list + detail + stats + registered-keys.
AuditEventFilter is shared by list and stats endpoints so all filter semantics
live in one place.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Outcome = Literal["success", "failure"]
Bucket = Literal["hour", "day"]


class AuditEventFilter(BaseModel):
    """Shared filter predicates for list + stats endpoints."""
    model_config = ConfigDict(extra="forbid")

    event_key: str | None = None
    """Exact event_key OR glob pattern (e.g. 'iam.orgs.*')."""
    category_code: str | None = None
    outcome: Outcome | None = None
    actor_user_id: str | None = None
    actor_session_id: str | None = None
    org_id: str | None = None
    workspace_id: str | None = None
    trace_id: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    q: str | None = None
    """Free-text substring match against metadata JSONB."""


class AuditEventListQuery(AuditEventFilter):
    cursor: str | None = None
    limit: int = Field(default=50, ge=1, le=1000)


class AuditEventRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    event_key: str
    event_label: str | None = None
    event_description: str | None = None
    category_code: str
    category_label: str | None = None
    actor_user_id: str | None = None
    actor_session_id: str | None = None
    org_id: str | None = None
    workspace_id: str | None = None
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    outcome: Outcome
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str

    @field_validator("created_at", mode="before")
    @classmethod
    def _coerce_timestamp(cls, v: object) -> object:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class AuditEventListResponse(BaseModel):
    items: list[AuditEventRow]
    next_cursor: str | None = None


class AuditEventStatsQuery(AuditEventFilter):
    bucket: Bucket = "hour"


class AuditEventStatsCountByKey(BaseModel):
    event_key: str
    count: int


class AuditEventStatsCountByOutcome(BaseModel):
    outcome: Outcome
    count: int


class AuditEventStatsCountByCategory(BaseModel):
    category_code: str
    count: int


class AuditEventStatsTimePoint(BaseModel):
    bucket: str
    count: int


class AuditEventStatsResponse(BaseModel):
    by_event_key: list[AuditEventStatsCountByKey]
    by_outcome: list[AuditEventStatsCountByOutcome]
    by_category: list[AuditEventStatsCountByCategory]
    time_series: list[AuditEventStatsTimePoint]


class AuditEventKeyRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    key: str
    label: str
    description: str | None = None
    category_code: str
    deprecated_at: str | None = None

    @field_validator("deprecated_at", mode="before")
    @classmethod
    def _coerce_timestamp(cls, v: object) -> object:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class AuditEventKeyListResponse(BaseModel):
    items: list[AuditEventKeyRow]
    total: int


# ── Funnel ────────────────────────────────────────────────────────────────

class FunnelRequest(BaseModel):
    steps: list[str] = Field(..., min_length=2, max_length=8)
    org_id: str | None = None
    since: datetime | None = None
    until: datetime | None = None


class FunnelStep(BaseModel):
    event_key: str
    users: int
    conversion_pct: float


class FunnelResponse(BaseModel):
    steps: list[FunnelStep]


# ── Retention ─────────────────────────────────────────────────────────────

class RetentionRetained(BaseModel):
    offset: int
    count: int
    pct: float


class RetentionCohort(BaseModel):
    cohort_period: str
    cohort_size: int
    retained: list[RetentionRetained]


class RetentionResponse(BaseModel):
    cohorts: list[RetentionCohort]

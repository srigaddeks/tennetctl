"""Request/response schemas for incidents sub-feature."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class IncidentStateTransition(BaseModel):
    """Request to change incident state."""
    state: Literal["acknowledged", "resolved", "closed"]
    summary: str | None = Field(None, description="Summary (required for closed)")
    root_cause: str | None = Field(None, description="Root cause (required for closed)")
    postmortem_ref: str | None = None


class IncidentCommentCreate(BaseModel):
    """Request to add comment to incident timeline."""
    body: str = Field(..., min_length=1, max_length=4096)


class GroupingRuleCreate(BaseModel):
    """Request to create/update grouping rule for a rule."""
    dedup_strategy: Literal["fingerprint", "label_set", "custom_key"] = "fingerprint"
    group_by: list[str] = Field(default_factory=list, description="Label keys to group by (for label_set)")
    group_window_seconds: int = Field(300, ge=60, le=3600)
    custom_template: str | None = Field(None, description="Jinja2 template (for custom_key)")
    is_active: bool = True


# Response schemas
class IncidentListItem(BaseModel):
    """Incident for list view."""
    id: str
    org_id: str
    group_key: str
    title: str
    severity_id: int
    severity_code: str
    severity_label: str
    state_id: int
    state_code: str
    state_label: str
    opened_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    linked_alert_count: int
    action_count: int
    created_at: datetime
    updated_at: datetime


class IncidentDetail(BaseModel):
    """Full incident with timeline summary."""
    id: str
    org_id: str
    group_key: str
    title: str
    severity_id: int
    severity_code: str
    severity_label: str
    state_id: int
    state_code: str
    state_label: str
    opened_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    ack_user_id: str | None
    resolved_by_user_id: str | None
    summary: str | None
    root_cause: str | None
    postmortem_ref: str | None
    action_count: int
    linked_alerts: list[dict] = Field(default_factory=list)
    timeline_events: list[dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TimelineEvent(BaseModel):
    """Single event in incident timeline."""
    id: str
    incident_id: str
    kind_id: int
    kind_code: str
    kind_label: str
    actor_user_id: str | None
    actor_email: str | None = None
    payload: dict = Field(default_factory=dict)
    occurred_at: datetime
    created_at: datetime


class GroupingRuleResponse(BaseModel):
    """Grouping rule for a rule."""
    rule_id: str
    dedup_strategy: str
    group_by: list[str]
    group_window_seconds: int
    custom_template: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

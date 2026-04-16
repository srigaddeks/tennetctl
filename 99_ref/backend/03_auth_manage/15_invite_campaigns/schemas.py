from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Campaign CRUD ─────────────────────────────────────────────────────────────

class CreateCampaignRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    campaign_type: str = Field(default="event", pattern=r"^(event|referral|form|import|other)$")
    default_scope: str = Field(default="platform", pattern=r"^(platform|organization|workspace)$")
    default_role: str | None = Field(default=None, max_length=50)
    default_org_id: str | None = Field(default=None, max_length=36)
    default_workspace_id: str | None = Field(default=None, max_length=36)
    default_expires_hours: int = Field(default=168, ge=1, le=2160)  # up to 90 days
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=5000)


class UpdateCampaignRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None, pattern=r"^(active|paused|closed|archived)$")
    default_role: str | None = Field(default=None, max_length=50)
    default_expires_hours: int | None = Field(default=None, ge=1, le=2160)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=5000)


# ── Bulk invite ───────────────────────────────────────────────────────────────

class BulkInviteEntry(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    role: str | None = None  # override campaign default


class BulkInviteRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    emails: list[str] = Field(default=[], max_length=500)
    entries: list[BulkInviteEntry] = Field(default=[], max_length=500)
    # Scope overrides (fall back to campaign defaults if not set)
    scope: str | None = Field(default=None, pattern=r"^(platform|organization|workspace)$")
    org_id: str | None = Field(default=None, max_length=36)
    workspace_id: str | None = Field(default=None, max_length=36)
    role: str | None = Field(default=None, max_length=50)
    expires_in_hours: int | None = Field(default=None, ge=1, le=2160)
    source_tag: str | None = Field(default=None, max_length=100)


class BulkInviteResultEntry(BaseModel):
    email: str
    status: str   # sent | skipped | error
    reason: str | None = None
    invitation_id: str | None = None


class BulkInviteResponse(BaseModel):
    sent: int
    skipped: int
    errors: int
    results: list[BulkInviteResultEntry]


# ── Campaign responses ────────────────────────────────────────────────────────

class CampaignResponse(BaseModel):
    id: str
    tenant_key: str
    code: str
    name: str
    description: str
    campaign_type: str
    status: str
    default_scope: str
    default_role: str | None
    default_org_id: str | None
    default_workspace_id: str | None
    default_expires_hours: int
    starts_at: datetime | None
    ends_at: datetime | None
    invite_count: int
    accepted_count: int
    notes: str | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None


class CampaignListResponse(BaseModel):
    campaigns: list[CampaignResponse]
    total: int

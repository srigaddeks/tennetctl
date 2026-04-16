from __future__ import annotations

from pydantic import BaseModel, Field


class CreateInvitationRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    scope: str = Field(..., pattern=r"^(platform|organization|workspace)$")
    org_id: str | None = None
    workspace_id: str | None = None
    role: str | None = None
    grc_role_code: str | None = Field(default=None, max_length=50)
    engagement_id: str | None = Field(default=None, max_length=36)
    framework_id: str | None = Field(default=None, max_length=36)
    framework_ids: list[str] | None = Field(default=None, max_length=50)
    engagement_ids: list[str] | None = Field(default=None, max_length=50)
    expires_in_hours: int = Field(default=72, ge=1, le=720)


class AcceptInvitationRequest(BaseModel):
    invite_token: str = Field(..., min_length=10)


class DeclineInvitationRequest(BaseModel):
    invite_token: str = Field(..., min_length=10)


class InvitationResponse(BaseModel):
    id: str
    email: str
    scope: str
    org_id: str | None = None
    workspace_id: str | None = None
    role: str | None = None
    grc_role_code: str | None = None
    engagement_id: str | None = None
    framework_id: str | None = None
    framework_ids: list[str] | None = None
    engagement_ids: list[str] | None = None
    status: str
    invited_by: str
    expires_at: str
    accepted_at: str | None = None
    accepted_by: str | None = None
    revoked_at: str | None = None
    revoked_by: str | None = None
    created_at: str
    updated_at: str


class InvitationCreatedResponse(InvitationResponse):
    invite_token: str


class InvitationListResponse(BaseModel):
    items: list[InvitationResponse]
    total: int
    page: int
    page_size: int


class InvitationStatsResponse(BaseModel):
    total: int
    pending: int
    accepted: int
    expired: int
    revoked: int
    declined: int


class InvitationPreviewResponse(BaseModel):
    """Public preview of an invitation — safe to return without authentication.

    Includes user_exists so the frontend can route new users to /register and
    returning users to /login before calling accept.
    """
    scope: str
    org_name: str | None = None
    workspace_name: str | None = None
    grc_role_code: str | None = None
    expires_at: str
    status: str
    email: str
    user_exists: bool


class InvitationAcceptedResponse(BaseModel):
    message: str
    scope: str
    org_id: str | None = None
    workspace_id: str | None = None
    role: str | None = None
    grc_role_code: str | None = None


# ── Bulk invite (no campaign) ─────────────────────────────────────────────────

class BulkCreateInvitationRequest(BaseModel):
    emails: list[str] = Field(default=[], max_length=500)
    scope: str = Field(default="platform", pattern=r"^(platform|organization|workspace)$")
    org_id: str | None = None
    workspace_id: str | None = None
    role: str | None = None
    grc_role_code: str | None = Field(default=None, max_length=50)
    expires_in_hours: int = Field(default=168, ge=1, le=2160)
    source_tag: str | None = Field(default=None, max_length=100)


class BulkInviteResultEntry(BaseModel):
    email: str
    status: str  # sent | skipped | error
    reason: str | None = None
    invitation_id: str | None = None


class BulkCreateInvitationResponse(BaseModel):
    sent: int
    skipped: int
    errors: int
    results: list[BulkInviteResultEntry]

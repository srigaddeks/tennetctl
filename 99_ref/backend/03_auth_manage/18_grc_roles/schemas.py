"""Pydantic v2 request/response schemas for GRC role management."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GrcRoleAssignmentResponse(BaseModel):
    """Single GRC role assignment in API response."""

    id: str
    org_id: str
    user_id: str
    grc_role_code: str
    role_name: str
    role_description: str | None = None
    email: str | None = None
    display_name: str | None = None
    assigned_by: str | None = None
    assigned_at: datetime
    active_grant_count: int = 0
    created_at: datetime


class GrcRoleAssignmentListResponse(BaseModel):
    """List of GRC role assignments."""

    items: list[GrcRoleAssignmentResponse]
    total: int


class AssignGrcRoleRequest(BaseModel):
    """Request body for POST /grc-roles — assign an org-level GRC role."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str = Field(..., min_length=36, max_length=36)
    grc_role_code: str = Field(
        ...,
        pattern=r"^grc_(practitioner|engineer|ciso|lead_auditor|staff_auditor|vendor)$",
    )


class GrcAccessGrantResponse(BaseModel):
    """Single access grant in API response."""

    id: str
    grc_role_assignment_id: str
    scope_type: str
    scope_id: str
    scope_name: str | None = None
    granted_by: str | None = None
    granted_at: datetime
    created_at: datetime


class GrcAccessGrantListResponse(BaseModel):
    """List of access grants."""

    items: list[GrcAccessGrantResponse]
    total: int


class CreateAccessGrantRequest(BaseModel):
    """Request body for POST /grc-roles/{id}/grants — grant scope access."""

    model_config = ConfigDict(str_strip_whitespace=True)

    scope_type: str = Field(..., pattern=r"^(workspace|framework|engagement)$")
    scope_id: str = Field(..., min_length=36, max_length=36)


class GrcTeamMemberResponse(BaseModel):
    """Team member with role and access grants."""

    assignment_id: str
    org_id: str
    user_id: str
    grc_role_code: str
    role_name: str
    email: str | None = None
    display_name: str | None = None
    assigned_at: datetime
    grants: list[GrcAccessGrantResponse] = []


class GrcTeamResponse(BaseModel):
    """Full GRC team view grouped by role category."""

    internal: list[GrcTeamMemberResponse] = []
    auditors: list[GrcTeamMemberResponse] = []
    vendors: list[GrcTeamMemberResponse] = []
    total: int = 0

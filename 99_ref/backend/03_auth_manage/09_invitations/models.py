from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InvitationRecord:
    id: str
    tenant_key: str
    email: str
    scope: str
    org_id: str | None
    workspace_id: str | None
    role: str | None
    status: str
    invited_by: str
    expires_at: str
    accepted_at: str | None
    accepted_by: str | None
    revoked_at: str | None
    revoked_by: str | None
    created_at: str
    updated_at: str
    grc_role_code: str | None = None
    engagement_id: str | None = None
    framework_id: str | None = None
    framework_ids: list[str] | None = None
    engagement_ids: list[str] | None = None

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CampaignRecord:
    id: str
    tenant_key: str
    code: str
    name: str
    description: str
    campaign_type: str          # event | referral | form | import | other
    status: str                 # active | paused | closed | archived
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

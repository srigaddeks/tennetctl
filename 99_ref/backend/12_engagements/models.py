from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import date, datetime

@dataclass(frozen=True)
class EngagementRecord:
    id: str
    tenant_key: str
    org_id: str
    engagement_code: str
    framework_id: str
    framework_deployment_id: str
    status_code: str
    target_completion_date: Optional[date]
    is_active: bool
    created_at: str
    updated_at: str
    created_by: Optional[str]


@dataclass(frozen=True)
class EngagementDetailRecord:
    id: str
    tenant_key: str
    org_id: str
    org_name: str
    engagement_code: str
    framework_id: str
    framework_deployment_id: str
    status_code: str
    status_name: str
    workspace_id: Optional[str] = None
    workspace_name: Optional[str] = None
    target_completion_date: Optional[str] = None
    total_controls_count: int = 0
    verified_controls_count: int = 0
    open_requests_count: int = 0
    engagement_name: Optional[str] = None
    auditor_firm: Optional[str] = None
    scope_description: Optional[str] = None
    audit_period_start: Optional[str] = None
    audit_period_end: Optional[str] = None
    lead_grc_sme: Optional[str] = None
    engagement_type: Optional[str] = None
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class AuditAccessTokenRecord:
    id: str
    engagement_id: str
    auditor_email: str
    expires_at: datetime
    is_revoked: bool
    created_at: datetime
    last_accessed_at: Optional[datetime] = None


@dataclass(frozen=True)
class AuditorRequestRecord:
    id: str
    engagement_id: str
    requested_by_token_id: str
    auditor_email: str
    control_id: Optional[str]
    request_status: str
    fulfilled_at: Optional[datetime]
    fulfilled_by: Optional[str]
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    request_description: Optional[str] = None
    response_notes: Optional[str] = None
    task_id: Optional[str] = None

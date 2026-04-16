from __future__ import annotations
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
from importlib import import_module

_task_schemas_module = import_module("backend.07_tasks.02_tasks.schemas")
TaskDetailResponse = _task_schemas_module.TaskDetailResponse
TaskListResponse = _task_schemas_module.TaskListResponse

_assess_schemas_module = import_module("backend.09_assessments.schemas")
AssessmentResponse = _assess_schemas_module.AssessmentResponse


class EngagementBase(BaseModel):
    engagement_code: str
    status_code: str = "setup"
    target_completion_date: Optional[date] = None
    engagement_name: str
    auditor_firm: str
    scope_description: Optional[str] = None
    audit_period_start: Optional[date] = None
    audit_period_end: Optional[date] = None
    lead_grc_sme: Optional[str] = None


class EngagementCreate(EngagementBase):
    framework_id: UUID
    framework_deployment_id: UUID
    engagement_type: Optional[str] = "readiness"  # readiness | audit


class EngagementUpdate(BaseModel):
    status_code: Optional[str] = None
    target_completion_date: Optional[date] = None
    engagement_name: Optional[str] = None
    auditor_firm: Optional[str] = None
    scope_description: Optional[str] = None
    audit_period_start: Optional[date] = None
    audit_period_end: Optional[date] = None
    lead_grc_sme: Optional[str] = None


class EngagementResponse(BaseModel):
    id: UUID
    tenant_key: str
    org_id: UUID
    org_name: str
    workspace_id: Optional[UUID] = None
    workspace_name: Optional[str] = None
    engagement_code: str
    framework_id: UUID
    framework_deployment_id: UUID
    status_code: str
    status_name: str
    total_controls_count: int = 0
    verified_controls_count: int = 0
    open_requests_count: int = 0
    target_completion_date: Optional[date] = None
    engagement_name: Optional[str] = None
    auditor_firm: Optional[str] = None
    scope_description: Optional[str] = None
    audit_period_start: Optional[date] = None
    audit_period_end: Optional[date] = None
    lead_grc_sme: Optional[str] = None
    engagement_type: Optional[str] = None
    open_requests_count: int
    verified_controls_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AuditorInviteRequest(BaseModel):
    email: str
    expires_in_days: int = 30


class AuditorInviteResponse(BaseModel):
    email: str
    invite_url: str
    expires_at: datetime


class AuditAccessTokenResponse(BaseModel):
    id: str
    engagement_id: str
    auditor_email: str
    expires_at: datetime
    is_revoked: bool
    last_accessed_at: Optional[datetime] = None
    created_at: datetime


class AuditorRequestResponse(BaseModel):
    id: str
    engagement_id: str
    requested_by_token_id: str
    auditor_email: Optional[str] = None
    control_id: Optional[str] = None
    request_status: str  # open | fulfilled | dismissed
    request_description: Optional[str] = None
    response_notes: Optional[str] = None
    task_id: Optional[str] = None
    fulfilled_at: Optional[datetime] = None
    fulfilled_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AuditorRequestFulfillRequest(BaseModel):
    action: str  # "fulfill" | "dismiss"
    attachment_ids: Optional[List[str]] = None
    response_notes: Optional[str] = None


class AuditorRequestRevokeRequest(BaseModel):
    response_notes: Optional[str] = None


class ControlVerificationRequest(BaseModel):
    outcome: str  # verified | qualified | failed
    observations: Optional[str] = None
    finding_details: Optional[str] = None


class AuditorDocRequest(BaseModel):
    description: str


class EvidenceResponse(BaseModel):
    id: UUID
    filename: str
    content_type: str
    size: int
    created_at: datetime
    request_id: Optional[UUID] = None


class ControlDetailResponse(BaseModel):
    verification: Optional[dict] = None
    evidence: List[EvidenceResponse] = []


class EngagementTaskCreateRequest(BaseModel):
    task_type_code: str = Field(..., min_length=1, max_length=50)
    priority_code: str = Field(default="medium", max_length=50)
    entity_type: str | None = Field(default="engagement", max_length=50)
    entity_id: str | None = None
    assignee_user_id: str | None = None
    due_date: str | None = None
    start_date: str | None = None
    estimated_hours: float | None = Field(default=None, ge=0)
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    acceptance_criteria: str | None = None
    remediation_plan: str | None = None


class EngagementParticipantResponse(BaseModel):
    user_id: str
    display_name: str | None = None
    email: str | None = None
    membership_type_code: str | None = None


class EngagementAssessmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    assessment_type_code: str = Field(default="external_audit", max_length=50)
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None

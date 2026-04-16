from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GenerateReportRequest(BaseModel):
    report_type: str
    title: str | None = None
    org_id: str
    workspace_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    # parameters may include: framework_id, date_from, date_to, include_sections, top_n, etc.


class ReportSummaryResponse(BaseModel):
    id: str
    report_type: str
    title: str | None
    status_code: str
    word_count: int | None
    is_auto_generated: bool
    workspace_id: str | None = None
    parameters_json: dict[str, Any] = Field(default_factory=dict)
    trigger_entity_type: str | None = None
    trigger_entity_id: str | None = None
    created_at: str
    completed_at: str | None


class ReportResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str | None
    workspace_id: str | None
    report_type: str
    status_code: str
    title: str | None
    parameters_json: dict
    content_markdown: str | None
    word_count: int | None
    token_count: int | None
    generated_by_user_id: str | None
    job_id: str | None
    error_message: str | None
    is_auto_generated: bool
    trigger_entity_type: str | None
    trigger_entity_id: str | None
    created_at: str
    completed_at: str | None
    updated_at: str


class ReportListResponse(BaseModel):
    items: list[ReportSummaryResponse]
    total: int


class ReportJobStatusResponse(BaseModel):
    job_id: str
    report_id: str | None
    status_code: str
    error_message: str | None
    started_at: str | None
    completed_at: str | None
    created_at: str


class EnhanceSectionRequest(BaseModel):
    section_title: str | None = None  # None = enhance whole report
    current_section_markdown: str
    instruction: str
    org_id: str
    workspace_id: str | None = None


class SuggestAssessmentRequest(BaseModel):
    org_id: str
    workspace_id: str | None = None


class UpdateReportRequest(BaseModel):
    title: str | None = None
    content_markdown: str | None = None


class SubmitReportRequest(BaseModel):
    engagement_id: str
    submission_notes: str | None = None


class AuditReadinessControls(BaseModel):
    passed: int
    total: int


class AuditReadinessEvidence(BaseModel):
    complete: int
    total: int


class AuditReadinessResponse(BaseModel):
    framework_id: str
    controls_passing: AuditReadinessControls
    evidence_complete: AuditReadinessEvidence
    open_gaps: int
    auditor_access: str  # "Active" | "Inactive" | "Pending"
    readiness_pct: float  # 0-100

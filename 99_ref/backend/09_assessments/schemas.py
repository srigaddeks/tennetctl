from __future__ import annotations

from pydantic import BaseModel, Field


class CreateAssessmentRequest(BaseModel):
    org_id: str
    workspace_id: str | None = None
    framework_id: str | None = None
    assessment_type_code: str
    lead_assessor_id: str | None = None
    scheduled_start: str | None = None
    scheduled_end: str | None = None
    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    scope_notes: str | None = None


class UpdateAssessmentRequest(BaseModel):
    assessment_type_code: str | None = None
    assessment_status_code: str | None = None
    lead_assessor_id: str | None = None
    scheduled_start: str | None = None
    scheduled_end: str | None = None
    name: str | None = None
    description: str | None = None
    scope_notes: str | None = None


class AssessmentResponse(BaseModel):
    id: str
    tenant_key: str
    assessment_code: str
    org_id: str
    workspace_id: str | None
    framework_id: str | None
    assessment_type_code: str
    assessment_status_code: str
    lead_assessor_id: str | None
    scheduled_start: str | None
    scheduled_end: str | None
    actual_start: str | None
    actual_end: str | None
    is_locked: bool
    assessment_type_name: str | None
    assessment_status_name: str | None
    name: str | None
    description: str | None
    scope_notes: str | None
    finding_count: int
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None


class AssessmentListResponse(BaseModel):
    items: list[AssessmentResponse]
    total: int
    limit: int
    offset: int


class CreateFindingRequest(BaseModel):
    control_id: str | None = None
    risk_id: str | None = None
    severity_code: str
    finding_type: str = Field(
        default="observation",
        pattern=r"^(non_conformity|observation|opportunity|recommendation)$",
    )
    assigned_to: str | None = None
    remediation_due_date: str | None = None
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    recommendation: str | None = None


class UpdateFindingRequest(BaseModel):
    finding_status_code: str | None = None
    severity_code: str | None = None
    assigned_to: str | None = None
    remediation_due_date: str | None = None
    title: str | None = None
    description: str | None = None
    recommendation: str | None = None


class FindingResponse(BaseModel):
    id: str
    assessment_id: str
    control_id: str | None
    risk_id: str | None
    severity_code: str
    finding_type: str
    finding_status_code: str
    assigned_to: str | None
    remediation_due_date: str | None
    severity_name: str | None
    finding_status_name: str | None
    title: str | None
    description: str | None
    recommendation: str | None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None


class FindingListResponse(BaseModel):
    items: list[FindingResponse]
    total: int


class CreateFindingResponseRequest(BaseModel):
    response_text: str = Field(..., min_length=1)


class FindingResponseResponse(BaseModel):
    id: str
    finding_id: str
    responder_id: str
    response_text: str | None
    responded_at: str
    created_at: str


class FindingResponseListResponse(BaseModel):
    items: list[FindingResponseResponse]


class AssessmentSummaryMatrix(BaseModel):
    open: int = 0
    in_remediation: int = 0
    verified_closed: int = 0
    accepted: int = 0
    disputed: int = 0


class AssessmentSummaryResponse(BaseModel):
    assessment_id: str
    total_findings: int
    matrix: dict[str, AssessmentSummaryMatrix]


class DimensionItemResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool


class DimensionListResponse(BaseModel):
    items: list[DimensionItemResponse]

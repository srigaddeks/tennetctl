from __future__ import annotations

from pydantic import BaseModel, Field


class CreateRiskRequest(BaseModel):
    org_id: str
    workspace_id: str
    risk_code: str = Field(..., min_length=1, max_length=100)
    risk_category_code: str = Field(..., min_length=1, max_length=50)
    risk_level_code: str = Field(default="medium", min_length=1, max_length=50)
    treatment_type_code: str = Field(default="mitigate", max_length=50)
    source_type: str = Field(default="manual", pattern=r"^(manual|auto_control_failure|vendor_risk|incident)$")
    # EAV properties
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    notes: str | None = None
    owner_user_id: str | None = None
    business_impact: str | None = None
    properties: dict[str, str] | None = None


class UpdateRiskRequest(BaseModel):
    risk_category_code: str | None = Field(None, max_length=50)
    risk_level_code: str | None = Field(None, max_length=50)
    treatment_type_code: str | None = Field(None, max_length=50)
    risk_status: str | None = Field(None, pattern=r"^(identified|assessed|treating|accepted|closed)$")
    is_disabled: bool | None = None
    # EAV properties
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    notes: str | None = None
    owner_user_id: str | None = None
    business_impact: str | None = None
    properties: dict[str, str] | None = None


class RiskResponse(BaseModel):
    id: str
    tenant_key: str
    risk_code: str
    org_id: str
    workspace_id: str
    risk_category_code: str
    risk_level_code: str
    treatment_type_code: str
    source_type: str
    risk_status: str
    is_active: bool
    version: int = 1
    created_at: str
    updated_at: str
    created_by: str | None = None


class RiskDetailResponse(BaseModel):
    id: str
    tenant_key: str
    risk_code: str
    org_id: str
    workspace_id: str
    risk_category_code: str
    category_name: str | None = None
    risk_level_code: str
    risk_level_name: str | None = None
    risk_level_color: str | None = None
    treatment_type_code: str
    treatment_type_name: str | None = None
    source_type: str
    risk_status: str
    is_active: bool
    version: int = 1
    created_at: str
    updated_at: str
    created_by: str | None = None
    title: str | None = None
    description: str | None = None
    notes: str | None = None
    owner_user_id: str | None = None
    owner_display_name: str | None = None
    business_impact: str | None = None
    inherent_risk_score: int | None = None
    residual_risk_score: int | None = None
    linked_control_count: int = 0
    treatment_plan_status: str | None = None
    treatment_plan_target_date: str | None = None


class RiskListResponse(BaseModel):
    items: list[RiskDetailResponse]
    total: int


class HeatMapCell(BaseModel):
    likelihood_score: int
    impact_score: int
    risk_count: int
    risk_ids: list[str]


class HeatMapResponse(BaseModel):
    cells: list[HeatMapCell]


class RiskSummaryResponse(BaseModel):
    total_risks: int
    identified_count: int
    assessed_count: int
    treating_count: int
    accepted_count: int
    closed_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    open_count: int
    created_this_week: int
    closed_this_week: int


# ─── Group Assignment ───────────────────────────────────────────────────────


class CreateRiskGroupAssignmentRequest(BaseModel):
    group_id: str
    role: str = Field(default="responsible", pattern=r"^(responsible|accountable|consulted|informed)$")


class RiskGroupAssignmentResponse(BaseModel):
    id: str
    risk_id: str
    group_id: str
    group_name: str | None = None
    role: str
    assigned_by: str
    assigned_at: str


class RiskGroupAssignmentListResponse(BaseModel):
    items: list[RiskGroupAssignmentResponse]


# ─── Risk Appetite / Tolerance ───────────────────────────────────────────────


class UpsertRiskAppetiteRequest(BaseModel):
    org_id: str
    risk_category_code: str
    appetite_level_code: str = Field(default="medium", pattern=r"^(low|medium|high|very_high)$")
    tolerance_threshold: int = Field(ge=1, le=25, default=15)
    max_acceptable_score: int = Field(ge=1, le=25, default=10)
    description: str | None = None


class RiskAppetiteResponse(BaseModel):
    id: str
    org_id: str
    risk_category_code: str
    appetite_level_code: str
    tolerance_threshold: int = Field(ge=1, le=25)
    max_acceptable_score: int = Field(ge=1, le=25)
    description: str | None = None


class RiskAppetiteListResponse(BaseModel):
    items: list[RiskAppetiteResponse]


# ─── Scheduled Reviews ──────────────────────────────────────────────────────


class UpsertReviewScheduleRequest(BaseModel):
    review_frequency: str = Field(pattern=r"^(monthly|quarterly|semi_annual|annual|custom)$")
    next_review_date: str  # ISO date
    assigned_reviewer_id: str | None = None


class CompleteReviewRequest(BaseModel):
    next_review_date: str  # ISO date for next scheduled review


class ReviewScheduleResponse(BaseModel):
    id: str
    risk_id: str
    review_frequency: str
    next_review_date: str
    last_reviewed_at: str | None = None
    last_reviewed_by: str | None = None
    assigned_reviewer_id: str | None = None
    is_overdue: bool


class OverdueReviewResponse(BaseModel):
    id: str
    risk_id: str
    risk_title: str | None = None
    review_frequency: str
    next_review_date: str
    assigned_reviewer_id: str | None = None
    is_overdue: bool


class OverdueReviewListResponse(BaseModel):
    items: list[OverdueReviewResponse]


class ImportRiskError(BaseModel):
    row: int
    key: str | None = None
    field: str | None = None
    message: str


class ImportRisksResult(BaseModel):
    created: int
    updated: int
    skipped: int = 0
    warnings: list[str] = []
    errors: list[ImportRiskError] = []
    dry_run: bool = False

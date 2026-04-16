"""Pydantic schemas for the Framework Builder agent."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Session ────────────────────────────────────────────────────────────────────


class CreateSessionRequest(BaseModel):
    session_type: Literal["create", "enhance", "gap"] = "create"
    framework_id: str | None = None  # required for enhance and gap mode
    scope_org_id: str | None = None
    scope_workspace_id: str | None = None
    framework_name: str | None = None
    framework_type_code: str | None = None
    framework_category_code: str | None = None
    user_context: str | None = None
    attachment_ids: list[str] = Field(default_factory=list)


class PatchSessionRequest(BaseModel):
    user_context: str | None = None
    attachment_ids: list[str] | None = None
    node_overrides: dict[str, str] | None = None
    accepted_changes: list[dict[str, Any]] | None = None
    # Cherry-pick: allow client to replace proposed data before committing
    proposed_hierarchy: dict[str, Any] | None = None
    proposed_controls: list[dict[str, Any]] | None = None
    proposed_risks: list[dict[str, Any]] | None = None
    proposed_risk_mappings: list[dict[str, Any]] | None = None


class SessionResponse(BaseModel):
    id: str
    tenant_key: str
    user_id: str
    session_type: str
    status: str
    scope_org_id: str | None
    scope_workspace_id: str | None
    framework_id: str | None
    framework_name: str | None
    framework_type_code: str | None
    framework_category_code: str | None
    user_context: str | None
    attachment_ids: list[str]
    node_overrides: dict[str, str]
    proposed_hierarchy: dict | None
    proposed_controls: list | None
    proposed_risks: list | None
    proposed_risk_mappings: list | None
    enhance_diff: list | None
    accepted_changes: list | None
    job_id: str | None
    result_framework_id: str | None
    error_message: str | None
    activity_log: list[dict] = Field(default_factory=list)
    created_at: str
    updated_at: str


class SessionListResponse(BaseModel):
    items: list[SessionResponse]
    total: int


# ── Phase 3 Creation Request ───────────────────────────────────────────────────


class CreateFrameworkFromSessionRequest(BaseModel):
    """Sent when user clicks 'Create Framework' after approving Phase 1+2 proposals."""

    # All data comes from the session — this is just a trigger
    priority_code: str = "normal"


# ── Apply Enhancements Request ─────────────────────────────────────────────────


class ApplyEnhancementsRequest(BaseModel):
    """Sent when user approves selected enhance-mode changes."""

    accepted_changes: list[dict[str, Any]] = Field(default_factory=list)
    priority_code: str = "normal"


# ── Job Status Response ────────────────────────────────────────────────────────


class BuildJobStatusResponse(BaseModel):
    job_id: str
    status: str  # queued | running | completed | failed
    job_type: str
    creation_log: list[dict] = Field(default_factory=list)
    framework_id: str | None = None
    stats: dict | None = None
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


# ── Gap Analysis ───────────────────────────────────────────────────────────────


class GapAnalysisRequest(BaseModel):
    framework_id: str
    user_context: str | None = None
    attachment_ids: list[str] | None = None
    priority_code: str = "normal"


class GapFinding(BaseModel):
    severity: str  # "critical" | "high" | "medium" | "low"
    category: str  # "control_coverage" | "risk_coverage" | "criticality" | "automation" | "benchmark"
    title: str
    description: str
    requirement_code: str | None = None
    control_code: str | None = None


class BenchmarkComparison(BaseModel):
    profile: str  # e.g. "SOC 2 Type II"
    findings: list[str]
    score: float  # 0.0–1.0


class GapAnalysisReport(BaseModel):
    framework_id: str
    framework_name: str
    generated_at: str
    requirement_count: int
    control_count: int
    risk_count: int
    health_score: int  # 0–100
    automation_score: int  # 0–100
    risk_coverage_pct: int  # 0–100
    findings: list[GapFinding]
    benchmark: BenchmarkComparison | None


class GapAnalysisJobStatusResponse(BaseModel):
    job_id: str
    status: str
    report: GapAnalysisReport | None = None
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None

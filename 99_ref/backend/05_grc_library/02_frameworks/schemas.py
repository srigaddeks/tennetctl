from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CreateFrameworkRequest(BaseModel):
    framework_code: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9][a-z0-9_\-]{0,98}[a-z0-9]$",
    )
    framework_type_code: str = Field(..., min_length=1, max_length=50)
    framework_category_code: str = Field(..., min_length=1, max_length=50)
    scope_org_id: str | None = None
    scope_workspace_id: str | None = None
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    short_description: str | None = None
    publisher_type: str | None = None
    publisher_name: str | None = None
    logo_url: str | None = None
    documentation_url: str | None = None
    properties: dict[str, str] | None = None


class UpdateFrameworkRequest(BaseModel):
    framework_type_code: str | None = Field(None, min_length=1, max_length=50)
    framework_category_code: str | None = Field(None, min_length=1, max_length=50)
    approval_status: str | None = Field(
        None, pattern=r"^(draft|pending_review|approved|rejected|suspended)$"
    )
    is_marketplace_visible: bool | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    short_description: str | None = None
    publisher_type: str | None = None
    publisher_name: str | None = None
    logo_url: str | None = None
    documentation_url: str | None = None
    properties: dict[str, str] | None = None


class FrameworkResponse(BaseModel):
    id: str
    tenant_key: str
    framework_code: str
    framework_type_code: str
    type_name: str | None = None
    framework_category_code: str
    category_name: str | None = None
    scope_org_id: str | None = None
    scope_workspace_id: str | None = None
    approval_status: str
    is_marketplace_visible: bool
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None = None
    name: str | None = None
    description: str | None = None
    short_description: str | None = None
    publisher_type: str | None = None
    publisher_name: str | None = None
    logo_url: str | None = None
    documentation_url: str | None = None
    latest_version_code: str | None = None
    control_count: int = 0
    working_control_count: int = 0
    has_pending_changes: bool = False


class FrameworkListResponse(BaseModel):
    items: list[FrameworkResponse]
    total: int


# ── Selective Submit for Review ─────────────────────────────────────────────────


class SubmitForReviewRequest(BaseModel):
    requirement_ids: list[str] = Field(
        default_factory=list, description="List of requirement IDs to submit for review"
    )
    control_ids: list[str] = Field(
        default_factory=list, description="List of control IDs to submit for review"
    )
    notes: str | None = Field(
        default=None, description="Optional notes for the review submission"
    )


class ReviewSelectionResponse(BaseModel):
    framework_id: str
    requirement_ids: list[str] = Field(default_factory=list)
    control_ids: list[str] = Field(default_factory=list)
    notes: str | None = None
    submitted_at: str | None = None


class ApproveWithSelectionRequest(BaseModel):
    control_ids: list[str] = Field(
        default_factory=list,
        description="Specific control IDs to include in version snapshot",
    )


# ── Bundle Export / Import ────────────────────────────────────────────────────


class BundleRequirement(BaseModel):
    requirement_code: str
    name: str | None = None
    description: str | None = None
    sort_order: int = 0
    parent_requirement_code: str | None = None


class BundleControl(BaseModel):
    control_code: str
    name: str | None = None
    description: str | None = None
    guidance: str | None = None
    implementation_notes: str | None = None
    criticality_code: str | None = None
    control_type: str | None = None
    automation_potential: str | None = None
    control_category_code: str | None = None
    requirement_code: str | None = None
    tags: str | None = None
    implementation_guidance: str | None = None
    responsible_teams: str | None = None


class BundleGlobalRisk(BaseModel):
    risk_code: str
    title: str | None = None
    description: str | None = None
    short_description: str | None = None
    risk_category_code: str | None = None
    risk_level_code: str | None = None
    inherent_likelihood: int | None = None
    inherent_impact: int | None = None
    mitigation_guidance: str | None = None
    detection_guidance: str | None = None
    linked_control_codes: list[str] = []


class FrameworkBundle(BaseModel):
    """Portable bundle for export/import. UUIDs never included."""

    framework_code: str
    framework_type_code: str
    framework_category_code: str
    name: str | None = None
    description: str | None = None
    short_description: str | None = None
    publisher_type: str | None = None
    publisher_name: str | None = None
    documentation_url: str | None = None
    requirements: list[BundleRequirement] = []
    controls: list[BundleControl] = []
    global_risks: list[BundleGlobalRisk] = []


class BundleImportError(BaseModel):
    section: str  # "framework" | "requirements" | "controls" | "global_risks" | "risk_control_mappings"
    key: str | None = None
    field: str | None = None
    message: str


class BundleImportResult(BaseModel):
    framework_created: bool = False
    framework_updated: bool = False
    requirements_created: int = 0
    requirements_updated: int = 0
    controls_created: int = 0
    controls_updated: int = 0
    global_risks_created: int = 0
    global_risks_updated: int = 0
    risk_control_links_created: int = 0
    warnings: list[str] = []
    errors: list[BundleImportError] = []
    dry_run: bool = False


# ── Diff Viewer ───────────────────────────────────────────────────────────────


class ControlDiff(BaseModel):
    control_code: str
    control_name: str | None = None
    control_description: str | None = None
    status: Literal["added", "removed", "modified", "unchanged"]
    field_changes: dict[str, tuple[str | None, str | None]] = {}
    # {field_name: (base_value, compare_value)}


class RequirementDiff(BaseModel):
    requirement_code: str
    name: str | None = None
    description: str | None = None
    status: Literal["added", "removed", "modified", "unchanged"]
    controls: list[ControlDiff] = []


class FrameworkDiff(BaseModel):
    framework_id: str
    framework_code: str
    base_label: str  # e.g. "v1.2 (published)" or "current"
    compare_label: str
    requirements: list[RequirementDiff] = []
    controls_added: int = 0
    controls_removed: int = 0
    controls_modified: int = 0
    controls_unchanged: int = 0

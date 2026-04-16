"""Pydantic schemas for the Signal Spec Agent."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Session ────────────────────────────────────────────────────────────────────

class CreateSpecSessionRequest(BaseModel):
    connector_type_code: str = Field(..., description="Connector type for the signal (e.g. 'github')")
    source_dataset_id: str | None = Field(None, description="Dataset to use for schema extraction + feasibility")
    org_id: str | None = None
    workspace_id: str | None = None
    initial_prompt: str | None = Field(None, min_length=0, description="Optional initial signal idea")


class RefineRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User refinement message")


class ApproveSpecRequest(BaseModel):
    """Locks the spec and enqueues test dataset generation."""
    priority_code: str = "normal"
    auto_compose_threats: bool = True
    auto_build_library: bool = True


class UpdateMarkdownRequest(BaseModel):
    markdown: str = Field(..., min_length=1, description="Edited Markdown spec to parse back into JSON")


class UpdateMarkdownResponse(BaseModel):
    session_id: str
    spec_json: dict
    markdown: str
    parse_warnings: list[str] = []


class SpecSessionResponse(BaseModel):
    id: str
    tenant_key: str
    user_id: str
    org_id: str | None
    workspace_id: str | None
    signal_id: str | None
    connector_type_code: str | None
    source_dataset_id: str | None
    status: str
    current_spec: dict | None
    feasibility_result: dict | None
    conversation_history: list
    job_id: str | None
    error_message: str | None
    created_at: str
    updated_at: str


class SpecSessionListResponse(BaseModel):
    items: list[SpecSessionResponse]
    total: int


class SpecJobStatusResponse(BaseModel):
    job_id: str
    status: str          # queued | running | completed | failed
    job_type: str
    signal_id: str | None = None
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    output_json: dict | None = None


# ── Data Sufficiency ──────────────────────────────────────────────────────────

class GenerateTestDatasetRequest(BaseModel):
    """Generate a signal-specific test dataset from spec + data sufficiency."""
    session_id: str = Field(..., description="Signal spec session containing the spec")
    dataset_id: str = Field(..., description="Source dataset for structure templates")
    signal_id: str | None = Field(None, description="Optional: signal to link test dataset to")
    sufficiency_result: dict = Field(default_factory=dict, description="Optional: pre-computed sufficiency result")


class StructuralIssue(BaseModel):
    test_record_name: str = ""
    issue_type: str  # missing_field | extra_field | type_mismatch | nesting_error
    field_path: str = ""
    expected: str = ""
    actual: str = ""
    severity: str = "warning"  # critical | warning | info


class GenerateTestDatasetResponse(BaseModel):
    overall_status: str  # ready | needs_fixes | failed
    ready_for_codegen: bool
    test_record_count: int = 0
    scenario_coverage: dict = Field(default_factory=dict)
    generation: dict = Field(default_factory=dict)
    verification: dict = Field(default_factory=dict)
    saved_dataset_id: str | None = None
    saved_dataset_name: str | None = None
    linked_to_signal: str | None = None
    save_error: str | None = None


class DataSufficiencyRequest(BaseModel):
    """Check if dataset has enough data to build a signal."""
    dataset_id: str = Field(..., description="Dataset to check against")
    signal_description: str = Field(..., min_length=5, description="What the signal should check")
    required_fields: list[str] = Field(default_factory=list, description="Optional: specific field paths needed")


class FieldCheck(BaseModel):
    field_path: str
    required: bool = True
    status: str  # present | missing | inconsistent | partial
    found_in_records: list[str] = Field(default_factory=list)
    missing_from_records: list[str] = Field(default_factory=list)
    sample_values: list = Field(default_factory=list)
    notes: str = ""


class RecordCoverage(BaseModel):
    record_name: str
    has_all_required_fields: bool
    missing_fields: list[str] = Field(default_factory=list)
    extra_fields_available: list[str] = Field(default_factory=list)


class Disagreement(BaseModel):
    field_path: str
    primary_said: str
    verifier_says: str
    evidence: str = ""
    resolution: str = ""


class DataSufficiencyResponse(BaseModel):
    status: str  # sufficient | partial | insufficient
    confidence: str  # high | medium | low
    is_sufficient: bool
    field_checks: list[FieldCheck] = Field(default_factory=list)
    record_coverage: list[RecordCoverage] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    disagreements: list[Disagreement] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    summary: str = ""
    primary_check: dict = Field(default_factory=dict)
    verifier_check: dict = Field(default_factory=dict)

from __future__ import annotations

from pydantic import BaseModel, Field


class ControlSuggestionSchema(BaseModel):
    control_id: str
    control_code: str
    control_name: str | None
    control_category_code: str | None
    criticality_code: str | None
    framework_id: str
    framework_code: str
    framework_name: str | None
    suggested_link_type: str
    relevance_score: int
    rationale: str
    already_linked: bool


class SuggestControlsRequest(BaseModel):
    risk_id: str
    org_id: str
    workspace_id: str | None = None
    framework_ids: list[str] | None = None
    top_n: int = Field(default=10, ge=1, le=30)


class SuggestControlsResponse(BaseModel):
    risk_id: str
    risk_code: str
    risk_title: str | None
    suggestions: list[ControlSuggestionSchema]
    total_candidates_evaluated: int
    suggestion_error: str | None = None


class BulkLinkRequest(BaseModel):
    framework_id: str | None = None   # None = all frameworks deployed to the org
    risk_id: str | None = None        # None = all risks in workspace
    org_id: str
    workspace_id: str | None = None
    priority_code: str = "normal"
    dry_run: bool = False


class BulkLinkJobResponse(BaseModel):
    job_id: str
    status: str
    framework_id: str | None
    dry_run: bool


class JobStatusResponse(BaseModel):
    job_id: str
    status_code: str
    job_type: str
    progress_pct: int | None
    output_json: dict | None
    error_message: str | None
    created_at: str
    updated_at: str

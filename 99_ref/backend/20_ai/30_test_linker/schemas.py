from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ControlSuggestionSchema(BaseModel):
    control_id: str
    control_code: str
    confidence: float
    link_type: str
    rationale: str


class TestSuggestionSchema(BaseModel):
    test_id: str
    test_code: str
    confidence: float
    link_type: str
    rationale: str


class SuggestControlsRequest(BaseModel):
    test_id: str
    framework_id: str | None = None
    org_id: str | None = None
    workspace_id: str | None = None


class SuggestTestsRequest(BaseModel):
    control_id: str
    org_id: str | None = None
    workspace_id: str | None = None


class ApplySuggestionsForTestRequest(BaseModel):
    test_id: str
    suggestions: list[ControlSuggestionSchema]


class ApplySuggestionsForControlRequest(BaseModel):
    control_id: str
    suggestions: list[TestSuggestionSchema]


class ApplyResult(BaseModel):
    created: int
    skipped: int


class PendingTestControlMappingSchema(BaseModel):
    id: str
    control_test_id: str
    control_id: str
    link_type: str
    ai_confidence: float | None = None
    ai_rationale: str | None = None
    approval_status: str
    created_at: str
    created_by: str | None = None
    test_name: str | None = None
    test_code: str | None = None
    control_name: str | None = None
    control_code: str | None = None
    framework_id: str | None = None
    framework_code: str | None = None


class PendingTestControlMappingListResponse(BaseModel):
    items: list[PendingTestControlMappingSchema]
    total: int


class BulkLinkRequest(BaseModel):
    org_id: str
    workspace_id: str | None = None
    framework_id: str | None = None
    control_ids: list[str] | None = None
    test_ids: list[str] | None = None
    priority_code: str = "normal"
    dry_run: bool = False

    @model_validator(mode="after")
    def validate_scope(self) -> "BulkLinkRequest":
        if self.control_ids is not None and len(self.control_ids) == 0:
            self.control_ids = None
        if self.test_ids is not None and len(self.test_ids) == 0:
            self.test_ids = None
        return self


class BulkLinkJobResponse(BaseModel):
    job_id: str
    status: str
    framework_id: str | None
    control_count: int | None = None
    test_count: int | None = None
    dry_run: bool


class JobStatusResponse(BaseModel):
    job_id: str
    status_code: str
    job_type: str
    progress_pct: int | None = None
    output_json: dict | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str


class ListPendingMappingsQuery(BaseModel):
    org_id: str | None = None
    workspace_id: str | None = None
    framework_id: str | None = None
    control_ids: list[str] | None = None
    test_ids: list[str] | None = None
    created_after: str | None = None
    mine_only: bool = False
    limit: int = Field(default=200, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class BulkDecisionRequest(BaseModel):
    mapping_ids: list[str] = Field(min_length=1)
    reason: str | None = None


class BulkDecisionResponse(BaseModel):
    updated: int

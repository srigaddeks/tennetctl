from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTestExecutionRequest(BaseModel):
    control_test_id: str
    control_id: str | None = None
    result_status: str = Field(default="pending", pattern=r"^(pending|pass|fail|partial|not_applicable|error)$")
    execution_type: str = Field(default="manual", pattern=r"^(manual|automated|scheduled)$")
    notes: str | None = None
    evidence_summary: str | None = None
    score: int | None = Field(default=None, ge=0, le=100)


class UpdateTestExecutionRequest(BaseModel):
    result_status: str | None = Field(default=None, pattern=r"^(pending|pass|fail|partial|not_applicable|error)$")
    notes: str | None = None
    evidence_summary: str | None = None
    score: int | None = Field(default=None, ge=0, le=100)


class TestExecutionResponse(BaseModel):
    id: str
    control_test_id: str
    control_id: str | None = None
    tenant_key: str
    result_status: str
    execution_type: str
    executed_by: str | None = None
    executed_at: str
    notes: str | None = None
    evidence_summary: str | None = None
    score: int | None = None
    is_active: bool
    created_at: str
    updated_at: str
    test_code: str | None = None
    test_name: str | None = None


class TestExecutionListResponse(BaseModel):
    items: list[TestExecutionResponse]
    total: int

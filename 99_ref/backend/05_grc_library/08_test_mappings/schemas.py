from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTestMappingRequest(BaseModel):
    control_id: str
    is_primary: bool = False
    sort_order: int = Field(default=0)
    # Optional: when provided, auto-creates an evidence_collection task for the control
    auto_create_evidence_task: bool = False
    org_id: str | None = None
    workspace_id: str | None = None


class TestMappingResponse(BaseModel):
    id: str
    control_test_id: str
    control_id: str
    is_primary: bool
    sort_order: int
    created_at: str
    created_by: str | None = None
    control_code: str | None = None
    control_name: str | None = None
    framework_code: str | None = None


class TestMappingListResponse(BaseModel):
    items: list[TestMappingResponse]
    total: int

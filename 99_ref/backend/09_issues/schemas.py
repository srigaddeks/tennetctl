from __future__ import annotations

from pydantic import BaseModel, Field


class IssueResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None = None
    promoted_test_id: str | None = None
    control_test_id: str | None = None
    execution_id: str | None = None
    connector_id: str | None = None
    status_code: str
    severity_code: str
    issue_code: str
    test_code: str | None = None
    test_name: str | None = None
    result_summary: str | None = None
    result_details: list | None = None
    connector_type_code: str | None = None
    assigned_to: str | None = None
    remediated_at: str | None = None
    remediation_notes: str | None = None
    verified_at: str | None = None
    is_active: bool = True
    created_at: str
    updated_at: str
    closed_at: str | None = None


class IssueListResponse(BaseModel):
    items: list[IssueResponse]
    total: int


class UpdateIssueRequest(BaseModel):
    status_code: str | None = None
    severity_code: str | None = None
    assigned_to: str | None = None
    remediation_notes: str | None = None


class IssueStatsResponse(BaseModel):
    total: int = 0
    open: int = 0
    investigating: int = 0
    remediated: int = 0
    closed: int = 0
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_connector_type: dict[str, int] = Field(default_factory=dict)

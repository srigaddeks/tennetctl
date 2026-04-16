from __future__ import annotations

from pydantic import BaseModel


class PromotedTestResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None = None
    promotion_id: str | None = None
    source_signal_id: str | None = None
    source_policy_id: str | None = None
    source_library_id: str | None = None
    source_pack_id: str | None = None
    test_code: str
    test_type_code: str
    monitoring_frequency: str
    linked_asset_id: str | None = None
    connector_type_code: str | None = None
    connector_name: str | None = None
    policy_container_code: str | None = None
    policy_container_name: str | None = None
    version_number: int
    is_active: bool
    promoted_by: str
    promoted_at: str
    name: str | None = None
    description: str | None = None
    evaluation_rule: str | None = None
    signal_type: str | None = None
    integration_guide: str | None = None
    control_test_id: str | None = None
    created_at: str
    updated_at: str


class PromotedTestListResponse(BaseModel):
    items: list[PromotedTestResponse]
    total: int


class UpdatePromotedTestRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    linked_asset_id: str | None = None


class ExecutePromotedTestRequest(BaseModel):
    dataset_id: str | None = None  # optional — if not provided, uses most recent dataset for the linked connector


class ExecutePromotedTestResponse(BaseModel):
    test_id: str
    test_code: str
    result_status: str  # pass | fail | warning | error
    summary: str
    details: list[dict] = []
    metadata: dict = {}
    execution_id: str | None = None  # GRC test execution record ID
    executed_at: str
    task_created: bool = False  # whether a remediation task was auto-created
    task_id: str | None = None

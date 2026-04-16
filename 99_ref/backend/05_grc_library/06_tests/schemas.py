from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTestRequest(BaseModel):
    test_code: str = Field(..., min_length=1, max_length=100)
    test_type_code: str = Field(..., min_length=1, max_length=50)
    integration_type: str | None = None
    monitoring_frequency: str = Field(default="manual", pattern=r"^(realtime|hourly|daily|weekly|manual)$")
    is_platform_managed: bool = False
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    evaluation_rule: str | None = None
    signal_type: str | None = None
    integration_guide: str | None = None
    scope_org_id: str | None = None
    scope_workspace_id: str | None = None
    properties: dict[str, str] | None = None


class UpdateTestRequest(BaseModel):
    test_type_code: str | None = Field(None, min_length=1, max_length=50)
    integration_type: str | None = None
    monitoring_frequency: str | None = Field(None, pattern=r"^(realtime|hourly|daily|weekly|manual)$")
    is_platform_managed: bool | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    evaluation_rule: str | None = None
    signal_type: str | None = None
    integration_guide: str | None = None
    properties: dict[str, str] | None = None


class TestResponse(BaseModel):
    id: str
    tenant_key: str
    test_code: str
    test_type_code: str
    test_type_name: str | None = None
    integration_type: str | None = None
    monitoring_frequency: str
    is_platform_managed: bool
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None = None
    description: str | None = None
    evaluation_rule: str | None = None
    signal_type: str | None = None
    integration_guide: str | None = None
    mapped_control_count: int = 0
    scope_org_id: str | None = None
    scope_workspace_id: str | None = None


class TestListResponse(BaseModel):
    items: list[TestResponse]
    total: int

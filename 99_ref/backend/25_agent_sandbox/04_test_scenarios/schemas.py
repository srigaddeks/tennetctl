from __future__ import annotations

from pydantic import BaseModel, Field


class CreateScenarioRequest(BaseModel):
    scenario_code: str = Field(
        ..., min_length=2, max_length=100, pattern=r"^[a-z0-9_]{2,100}$"
    )
    scenario_type_code: str = Field(default="single_turn")
    workspace_id: str | None = None
    agent_id: str | None = None
    properties: dict[str, str] = Field(
        default_factory=dict, description="EAV: name, description"
    )


class UpdateScenarioRequest(BaseModel):
    scenario_type_code: str | None = None
    agent_id: str | None = None
    properties: dict[str, str] | None = None


class AddTestCaseRequest(BaseModel):
    input_messages: list[dict] = Field(default_factory=list)
    initial_context: dict = Field(default_factory=dict)
    expected_behavior: dict = Field(default_factory=dict)
    evaluation_method_code: str = Field(default="deterministic")
    evaluation_config: dict = Field(default_factory=dict)


class TestCaseResponse(BaseModel):
    id: str
    scenario_id: str
    case_index: int
    input_messages: list[dict] = Field(default_factory=list)
    initial_context: dict = Field(default_factory=dict)
    expected_behavior: dict = Field(default_factory=dict)
    evaluation_method_code: str
    evaluation_config: dict = Field(default_factory=dict)
    is_active: bool
    created_at: str


class ScenarioResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None = None
    scenario_code: str
    scenario_type_code: str
    agent_id: str | None = None
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None = None
    description: str | None = None
    test_cases: list[TestCaseResponse] | None = None
    properties: dict[str, str] | None = None


class ScenarioListResponse(BaseModel):
    items: list[ScenarioResponse]
    total: int

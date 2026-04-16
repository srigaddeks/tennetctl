from __future__ import annotations

from pydantic import BaseModel, Field


class CreateAgentRequest(BaseModel):
    agent_code: str = Field(
        ..., min_length=2, max_length=100, pattern=r"^[a-z0-9_]{2,100}$"
    )
    workspace_id: str | None = None
    graph_type: str = Field(default="sequential", pattern=r"^(sequential|branching|cyclic)$")
    llm_model_id: str | None = None
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_iterations: int = Field(default=20, ge=1, le=1000)
    max_tokens_budget: int = Field(default=50000, ge=100, le=10000000)
    max_tool_calls: int = Field(default=100, ge=0, le=10000)
    max_duration_ms: int = Field(default=300000, ge=1000, le=3600000)
    max_cost_usd: float = Field(default=1.0, ge=0.0, le=1000.0)
    requires_approval: bool = False
    properties: dict[str, str] = Field(
        ..., description="Must include 'name' and 'graph_source'"
    )


class UpdateAgentRequest(BaseModel):
    graph_type: str | None = Field(None, pattern=r"^(sequential|branching|cyclic)$")
    llm_model_id: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_iterations: int | None = Field(None, ge=1, le=1000)
    max_tokens_budget: int | None = Field(None, ge=100, le=10000000)
    max_tool_calls: int | None = Field(None, ge=0, le=10000)
    max_duration_ms: int | None = Field(None, ge=1000, le=3600000)
    max_cost_usd: float | None = Field(None, ge=0.0, le=1000.0)
    requires_approval: bool | None = None
    properties: dict[str, str] | None = None


class BindToolRequest(BaseModel):
    tool_id: str = Field(..., description="Tool ID to bind")
    sort_order: int = Field(default=0, ge=0)


class AgentResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None = None
    agent_code: str
    version_number: int
    agent_status_code: str
    agent_status_name: str | None = None
    graph_type: str
    llm_model_id: str | None = None
    temperature: float
    max_iterations: int
    max_tokens_budget: int
    max_tool_calls: int
    max_duration_ms: int
    max_cost_usd: float
    requires_approval: bool
    python_hash: str | None = None
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None = None
    description: str | None = None
    graph_source: str | None = None
    properties: dict[str, str] | None = None


class AgentListResponse(BaseModel):
    items: list[AgentResponse]
    total: int


class AgentVersionResponse(BaseModel):
    version_number: int
    agent_status_code: str
    python_hash: str | None = None
    created_at: str
    created_by: str | None = None

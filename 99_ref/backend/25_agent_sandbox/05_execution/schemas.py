from __future__ import annotations

from pydantic import BaseModel, Field


class ExecuteAgentRequest(BaseModel):
    input_messages: list[dict] = Field(default_factory=list, description="Initial messages")
    initial_context: dict = Field(default_factory=dict, description="Additional context")


class ResumeAgentRequest(BaseModel):
    human_response: str = Field(..., description="Response to the agent's question")


class AgentRunResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None = None
    agent_id: str
    execution_status_code: str
    execution_status_name: str | None = None
    tokens_used: int = 0
    tool_calls_made: int = 0
    llm_calls_made: int = 0
    cost_usd: float = 0.0
    iterations_used: int = 0
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    execution_time_ms: int | None = None
    langfuse_trace_id: str | None = None
    test_run_id: str | None = None
    agent_code_snapshot: str | None = None
    version_snapshot: int | None = None
    agent_name: str | None = None
    created_at: str
    created_by: str | None = None


class AgentRunListResponse(BaseModel):
    items: list[AgentRunResponse]
    total: int


class AgentRunStepResponse(BaseModel):
    id: str
    agent_run_id: str
    step_index: int
    node_name: str
    step_type: str
    transition: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_ms: int | None = None
    error_message: str | None = None
    started_at: str
    completed_at: str | None = None


class CompileCheckRequest(BaseModel):
    graph_source: str = Field(..., min_length=10, description="Python source code")


class CompileCheckResponse(BaseModel):
    success: bool
    errors: list[str] | None = None
    handler_names: list[str] | None = None

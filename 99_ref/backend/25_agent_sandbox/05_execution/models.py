from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentRunRecord:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None
    agent_id: str
    execution_status_code: str
    execution_status_name: str | None
    tokens_used: int
    tool_calls_made: int
    llm_calls_made: int
    cost_usd: float
    iterations_used: int
    error_message: str | None
    started_at: str | None
    completed_at: str | None
    execution_time_ms: int | None
    langfuse_trace_id: str | None
    test_run_id: str | None
    agent_code_snapshot: str | None
    version_snapshot: int | None
    agent_name: str | None
    created_at: str
    created_by: str | None


@dataclass(frozen=True)
class AgentRunStepRecord:
    id: str
    agent_run_id: str
    step_index: int
    node_name: str
    step_type: str
    transition: str | None
    tokens_used: int
    cost_usd: float
    duration_ms: int | None
    error_message: str | None
    started_at: str
    completed_at: str | None

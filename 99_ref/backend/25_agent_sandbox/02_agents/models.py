from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentRecord:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None
    agent_code: str
    version_number: int
    agent_status_code: str
    agent_status_name: str | None
    graph_type: str
    llm_model_id: str | None
    temperature: float
    max_iterations: int
    max_tokens_budget: int
    max_tool_calls: int
    max_duration_ms: int
    max_cost_usd: float
    requires_approval: bool
    python_hash: str | None
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None
    description: str | None

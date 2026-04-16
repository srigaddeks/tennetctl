from __future__ import annotations
from pydantic import BaseModel

class AISummaryResponse(BaseModel):
    total_conversations: int
    total_messages: int
    total_agent_runs: int
    total_tokens_used: int
    total_cost_usd: float
    active_approvals: int
    guardrail_events_today: int
    jobs_queued: int
    jobs_running: int

class AgentRunStats(BaseModel):
    agent_type_code: str
    agent_type_name: str | None = None
    run_count: int
    total_tokens: int
    total_cost_usd: float
    avg_duration_ms: float | None = None
    error_rate_pct: float | None = None

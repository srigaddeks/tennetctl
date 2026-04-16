from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenBudgetRecord:
    id: str
    tenant_key: str
    user_id: str
    period_code: str
    max_tokens: int
    max_cost_usd: float
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class TokenUsageSummary:
    user_id: str
    tenant_key: str
    period_code: str
    period_name: str
    tokens_used: int
    cost_usd: float
    max_tokens: int | None
    max_cost_usd: float | None
    token_utilization_pct: float | None
    cost_utilization_pct: float | None


@dataclass(frozen=True)
class BudgetCheckResult:
    allowed: bool
    reason: str | None
    tokens_used: int
    tokens_limit: int | None
    cost_used: float
    cost_limit: float | None
    retry_after_seconds: int | None

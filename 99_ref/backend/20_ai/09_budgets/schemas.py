from __future__ import annotations

from pydantic import BaseModel, Field


class TokenBudgetResponse(BaseModel):
    id: str
    tenant_key: str
    user_id: str
    period_code: str
    max_tokens: int
    max_cost_usd: float
    is_active: bool
    created_at: str
    updated_at: str


class TokenBudgetListResponse(BaseModel):
    items: list[TokenBudgetResponse]
    total: int


class UpsertBudgetRequest(BaseModel):
    period_code: str = Field(..., description="daily | monthly")
    max_tokens: int = Field(..., ge=0)
    max_cost_usd: float = Field(..., ge=0)
    is_active: bool = True


class UsageSummaryResponse(BaseModel):
    user_id: str
    tenant_key: str
    period_code: str
    period_name: str
    tokens_used: int
    cost_usd: float
    max_tokens: int | None = None
    max_cost_usd: float | None = None
    token_utilization_pct: float | None = None
    cost_utilization_pct: float | None = None


class BudgetCheckResponse(BaseModel):
    allowed: bool
    reason: str | None = None
    tokens_used: int
    tokens_limit: int | None = None
    cost_used: float
    cost_limit: float | None = None
    retry_after_seconds: int | None = None

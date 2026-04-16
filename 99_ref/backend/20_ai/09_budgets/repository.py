from __future__ import annotations

import asyncpg

from .models import BudgetCheckResult, TokenBudgetRecord, TokenUsageSummary


class BudgetRepository:
    _SCHEMA = '"20_ai"'
    _BUDGETS = f'{_SCHEMA}."28_fct_token_budgets"'
    _USAGE = f'{_SCHEMA}."29_trx_token_usage"'
    _USAGE_VIEW = f'{_SCHEMA}."63_vw_token_usage_summary"'

    async def get_budget(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        period_code: str,
    ) -> TokenBudgetRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, user_id::text, period_code,
                   max_tokens, max_cost_usd::float, is_active,
                   created_at::text, updated_at::text
            FROM {self._BUDGETS}
            WHERE user_id = $1 AND period_code = $2 AND is_active = TRUE
            """,
            user_id, period_code,
        )
        return TokenBudgetRecord(**dict(row)) if row else None

    async def list_budgets(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        user_id: str | None = None,
    ) -> list[TokenBudgetRecord]:
        conditions = ["tenant_key = $1"]
        params: list = [tenant_key]
        if user_id:
            conditions.append(f"user_id = $2")
            params.append(user_id)
        rows = await connection.fetch(
            f"""
            SELECT id::text, tenant_key, user_id::text, period_code,
                   max_tokens, max_cost_usd::float, is_active,
                   created_at::text, updated_at::text
            FROM {self._BUDGETS}
            WHERE {" AND ".join(conditions)}
            ORDER BY user_id, period_code
            """,
            *params,
        )
        return [TokenBudgetRecord(**dict(r)) for r in rows]

    async def upsert_budget(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        user_id: str,
        period_code: str,
        max_tokens: int,
        max_cost_usd: float,
        is_active: bool,
    ) -> TokenBudgetRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {self._BUDGETS}
                (tenant_key, user_id, period_code, max_tokens, max_cost_usd, is_active)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id, period_code)
            DO UPDATE SET
                max_tokens = EXCLUDED.max_tokens,
                max_cost_usd = EXCLUDED.max_cost_usd,
                is_active = EXCLUDED.is_active,
                updated_at = NOW()
            RETURNING id::text, tenant_key, user_id::text, period_code,
                      max_tokens, max_cost_usd::float, is_active,
                      created_at::text, updated_at::text
            """,
            tenant_key, user_id, period_code, max_tokens, max_cost_usd, is_active,
        )
        return TokenBudgetRecord(**dict(row))

    async def get_current_usage(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        period_code: str,
    ) -> tuple[int, float]:
        """Returns (tokens_used, cost_usd) for the current period window."""
        if period_code == "daily":
            window = "DATE_TRUNC('day', NOW())"
        else:
            window = "DATE_TRUNC('month', NOW())"
        row = await connection.fetchrow(
            f"""
            SELECT COALESCE(SUM(tokens_used), 0)::int AS tokens_used,
                   COALESCE(SUM(cost_usd), 0)::float AS cost_usd
            FROM {self._USAGE}
            WHERE user_id = $1 AND recorded_at >= {window}
            """,
            user_id,
        )
        return row["tokens_used"], row["cost_usd"]

    async def record_usage(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        agent_run_id: str | None,
        tokens_used: int,
        cost_usd: float,
        model_id: str | None,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {self._USAGE}
                (user_id, tenant_key, agent_run_id, tokens_used, cost_usd, model_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            user_id, tenant_key, agent_run_id, tokens_used, cost_usd, model_id,
        )

    async def get_usage_summary(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
    ) -> list[TokenUsageSummary]:
        rows = await connection.fetch(
            f"""
            SELECT user_id::text, tenant_key, period_code, period_name,
                   tokens_used::int, cost_usd::float,
                   max_tokens, max_cost_usd::float,
                   token_utilization_pct::float, cost_utilization_pct::float
            FROM {self._USAGE_VIEW}
            WHERE user_id = $1 AND tenant_key = $2
            """,
            user_id, tenant_key,
        )
        return [TokenUsageSummary(**dict(r)) for r in rows]

    async def check_budget(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        estimated_tokens: int = 0,
    ) -> BudgetCheckResult:
        """Check if user is within budget for both daily and monthly periods."""
        for period in ("daily", "monthly"):
            budget = await self.get_budget(connection, user_id=user_id, period_code=period)
            if not budget:
                continue
            tokens_used, cost_used = await self.get_current_usage(connection, user_id=user_id, period_code=period)
            if tokens_used + estimated_tokens > budget.max_tokens:
                reset_seconds = 86400 if period == "daily" else 3600 * 24 * 30
                return BudgetCheckResult(
                    allowed=False,
                    reason=f"Token budget exceeded for {period} period ({tokens_used:,}/{budget.max_tokens:,} tokens)",
                    tokens_used=tokens_used,
                    tokens_limit=budget.max_tokens,
                    cost_used=cost_used,
                    cost_limit=budget.max_cost_usd,
                    retry_after_seconds=reset_seconds,
                )
        return BudgetCheckResult(
            allowed=True, reason=None,
            tokens_used=0, tokens_limit=None,
            cost_used=0.0, cost_limit=None,
            retry_after_seconds=None,
        )

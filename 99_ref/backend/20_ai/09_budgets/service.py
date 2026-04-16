from __future__ import annotations

import uuid
import datetime
from importlib import import_module

from .models import BudgetCheckResult, TokenBudgetRecord
from .repository import BudgetRepository
from .schemas import (
    BudgetCheckResponse,
    TokenBudgetListResponse,
    TokenBudgetResponse,
    UpsertBudgetRequest,
    UsageSummaryResponse,
)

_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_constants_module = import_module("backend.20_ai.constants")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ForbiddenError = _errors_module.AuthorizationError
RateLimitError = _errors_module.RateLimitError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AIAuditEventType = _constants_module.AIAuditEventType
require_permission = _perm_check_module.require_permission

_DEFAULT_DAILY_TOKENS = 100_000
_DEFAULT_DAILY_COST = 5.0
_DEFAULT_MONTHLY_TOKENS = 2_000_000
_DEFAULT_MONTHLY_COST = 100.0


def _to_response(r: TokenBudgetRecord) -> TokenBudgetResponse:
    return TokenBudgetResponse(
        id=r.id, tenant_key=r.tenant_key, user_id=r.user_id,
        period_code=r.period_code, max_tokens=r.max_tokens,
        max_cost_usd=r.max_cost_usd, is_active=r.is_active,
        created_at=r.created_at, updated_at=r.updated_at,
    )


@instrument_class_methods(
    namespace="ai.budgets.service",
    logger_name="backend.ai.budgets.instrumentation",
)
class BudgetService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = BudgetRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.ai.budgets")

    async def check_budget(
        self,
        *,
        user_id: str,
        estimated_tokens: int = 0,
    ) -> BudgetCheckResult:
        """Called before every agent run. Raises TooManyRequestsError if over budget."""
        async with self._database_pool.acquire() as conn:
            result = await self._repository.check_budget(
                conn, user_id=user_id, estimated_tokens=estimated_tokens
            )
        if not result.allowed:
            self._logger.warning("Budget exceeded for user %s: %s", user_id, result.reason)
        return result

    async def enforce_budget(
        self,
        *,
        user_id: str,
        tenant_key: str,
        estimated_tokens: int = 0,
    ) -> None:
        """Enforce budget — raises TooManyRequestsError if over limit. Call before agent execution."""
        result = await self.check_budget(user_id=user_id, estimated_tokens=estimated_tokens)
        if not result.allowed:
            async with self._database_pool.acquire() as conn:
                await self._audit_writer.write_entry(conn, AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="user",
                    entity_id=user_id,
                    event_type=AIAuditEventType.BUDGET_EXCEEDED,
                    event_category="ai",
                    actor_id=user_id,
                    actor_type="user",
                    properties={"reason": result.reason or "", "estimated_tokens": str(estimated_tokens)},
                    occurred_at=datetime.datetime.utcnow(),
                ))
            raise RateLimitError(result.reason or "Token budget exceeded")

    async def record_usage(
        self,
        *,
        user_id: str,
        tenant_key: str,
        agent_run_id: str | None,
        tokens_used: int,
        cost_usd: float,
        model_id: str | None,
    ) -> None:
        """Record actual token usage after agent run completes."""
        async with self._database_pool.acquire() as conn:
            await self._repository.record_usage(
                conn,
                user_id=user_id,
                tenant_key=tenant_key,
                agent_run_id=agent_run_id,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                model_id=model_id,
            )
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                entity_type="user",
                entity_id=user_id,
                event_type=AIAuditEventType.BUDGET_USAGE_RECORDED,
                event_category="ai",
                actor_id=user_id,
                actor_type="user",
                properties={
                    "tokens_used": str(tokens_used),
                    "cost_usd": str(cost_usd),
                    "model_id": model_id or "",
                    "agent_run_id": agent_run_id or "",
                },
                occurred_at=datetime.datetime.utcnow(),
            ))

    async def get_my_usage(
        self,
        *,
        user_id: str,
        tenant_key: str,
    ) -> list[UsageSummaryResponse]:
        async with self._database_pool.acquire() as conn:
            summaries = await self._repository.get_usage_summary(conn, user_id=user_id, tenant_key=tenant_key)
        return [
            UsageSummaryResponse(
                user_id=s.user_id, tenant_key=s.tenant_key,
                period_code=s.period_code, period_name=s.period_name,
                tokens_used=s.tokens_used, cost_usd=s.cost_usd,
                max_tokens=s.max_tokens, max_cost_usd=s.max_cost_usd,
                token_utilization_pct=s.token_utilization_pct,
                cost_utilization_pct=s.cost_utilization_pct,
            )
            for s in summaries
        ]

    async def list_budgets(
        self,
        *,
        user_id: str,
        tenant_key: str,
        target_user_id: str | None = None,
        caller_id: str,
    ) -> TokenBudgetListResponse:
        # Admin can see all users; regular user can only see their own
        async with self._database_pool.acquire() as conn:
            if target_user_id and target_user_id != caller_id:
                await require_permission(conn, caller_id, "ai_copilot.admin")
            records = await self._repository.list_budgets(
                conn, tenant_key=tenant_key, user_id=target_user_id or caller_id
            )
        items = [_to_response(r) for r in records]
        return TokenBudgetListResponse(items=items, total=len(items))

    async def upsert_budget(
        self,
        *,
        caller_id: str,
        tenant_key: str,
        target_user_id: str,
        request: UpsertBudgetRequest,
    ) -> TokenBudgetResponse:
        # Only admin can set budgets for other users
        async with self._database_pool.acquire() as conn:
            if target_user_id != caller_id:
                await require_permission(conn, caller_id, "ai_copilot.admin")
            record = await self._repository.upsert_budget(
                conn,
                tenant_key=tenant_key,
                user_id=target_user_id,
                period_code=request.period_code,
                max_tokens=request.max_tokens,
                max_cost_usd=request.max_cost_usd,
                is_active=request.is_active,
            )
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                entity_type="user",
                entity_id=target_user_id,
                event_type=AIAuditEventType.BUDGET_UPDATED,
                event_category="ai",
                actor_id=caller_id,
                actor_type="user",
                properties={
                    "period_code": request.period_code,
                    "max_tokens": str(request.max_tokens),
                    "max_cost_usd": str(request.max_cost_usd),
                },
                occurred_at=datetime.datetime.utcnow(),
            ))
        return _to_response(record)

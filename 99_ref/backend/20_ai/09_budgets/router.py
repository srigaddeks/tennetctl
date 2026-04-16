from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_service_module = import_module("backend.20_ai.09_budgets.service")
_schemas_module = import_module("backend.20_ai.09_budgets.schemas")
_deps_module = import_module("backend.20_ai.09_budgets.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims
BudgetService = _service_module.BudgetService
TokenBudgetListResponse = _schemas_module.TokenBudgetListResponse
TokenBudgetResponse = _schemas_module.TokenBudgetResponse
UpsertBudgetRequest = _schemas_module.UpsertBudgetRequest
UsageSummaryResponse = _schemas_module.UsageSummaryResponse
BudgetCheckResponse = _schemas_module.BudgetCheckResponse
get_budget_service = _deps_module.get_budget_service

router = InstrumentedAPIRouter(prefix="/api/v1/ai/budgets", tags=["ai-budgets"])


@router.get("/me/usage", response_model=list[UsageSummaryResponse])
async def get_my_usage(
    service: Annotated[BudgetService, Depends(get_budget_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> list[UsageSummaryResponse]:
    return await service.get_my_usage(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
    )


@router.get("/me/check", response_model=BudgetCheckResponse)
async def check_my_budget(
    service: Annotated[BudgetService, Depends(get_budget_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    estimated_tokens: int = Query(default=0, ge=0),
) -> BudgetCheckResponse:
    result = await service.check_budget(user_id=claims.subject, estimated_tokens=estimated_tokens)
    return BudgetCheckResponse(
        allowed=result.allowed, reason=result.reason,
        tokens_used=result.tokens_used, tokens_limit=result.tokens_limit,
        cost_used=result.cost_used, cost_limit=result.cost_limit,
        retry_after_seconds=result.retry_after_seconds,
    )


@router.get("", response_model=TokenBudgetListResponse)
async def list_budgets(
    service: Annotated[BudgetService, Depends(get_budget_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    user_id: str | None = Query(None, description="Filter by user (admin only for other users)"),
) -> TokenBudgetListResponse:
    return await service.list_budgets(
        user_id=user_id,
        tenant_key=claims.tenant_key,
        target_user_id=user_id,
        caller_id=claims.subject,
    )


@router.put("/{user_id}", response_model=TokenBudgetResponse)
async def upsert_budget(
    user_id: str,
    request: UpsertBudgetRequest,
    service: Annotated[BudgetService, Depends(get_budget_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> TokenBudgetResponse:
    return await service.upsert_budget(
        caller_id=claims.subject,
        tenant_key=claims.tenant_key,
        target_user_id=user_id,
        request=request,
    )

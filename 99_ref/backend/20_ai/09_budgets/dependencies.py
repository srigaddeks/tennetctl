from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.20_ai.09_budgets.service")
BudgetService = _service_module.BudgetService


def get_budget_service(request: Request) -> BudgetService:
    return BudgetService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

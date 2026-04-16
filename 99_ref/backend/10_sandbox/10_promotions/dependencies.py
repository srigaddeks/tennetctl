from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.10_sandbox.10_promotions.service")
PromotionService = _service_module.PromotionService


def get_promotion_service(request: Request) -> PromotionService:
    return PromotionService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )

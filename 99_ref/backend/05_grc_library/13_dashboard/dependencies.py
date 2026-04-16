from __future__ import annotations

from typing import Annotated
from fastapi import Depends, Request
from .service import DashboardService


async def get_dashboard_service(request: Request) -> DashboardService:
    app_state = request.app.state
    return DashboardService(
        settings=app_state.settings,
        database_pool=app_state.database_pool,
        cache=app_state.cache,
    )

from __future__ import annotations

from fastapi import Request

from .service import RiskAdvisorService


def get_risk_advisor_service(request: Request) -> RiskAdvisorService:
    return RiskAdvisorService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
    )

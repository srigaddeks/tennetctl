from __future__ import annotations

from importlib import import_module
from typing import Annotated
from fastapi import Depends
from .dependencies import get_dashboard_service
from .service import DashboardService
from .schemas import GrcDashboardResponse, EngineerDashboardResponse, ExecutiveDashboardResponse



_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/grc", tags=["grc-dashboard"])

@router.get("/dashboard", response_model=GrcDashboardResponse)
async def get_dashboard(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    org_id: str | None = None,
    engagement_id: str | None = None,
    claims=Depends(get_current_access_claims),
) -> GrcDashboardResponse:
    """
    Get the GRC Lead Dashboard operational overview.
    Aggregates trust score, test stats, task forecast, and framework status.
    """
    return await service.get_dashboard(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        engagement_id=engagement_id
    )

@router.get("/engineer/dashboard", response_model=EngineerDashboardResponse)
async def get_engineer_dashboard(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    org_id: str | None = None,
    claims=Depends(get_current_access_claims),
) -> EngineerDashboardResponse:
    """
    Get the Engineering persona operational overview.
    Aggregates owned controls, personal task status breakdown, and upcoming deadlines.
    """
    return await service.get_engineer_dashboard(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id
    )


@router.get("/executive/dashboard", response_model=ExecutiveDashboardResponse)
async def get_executive_dashboard(
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
    org_id: str | None = None,
    claims=Depends(get_current_access_claims),
) -> ExecutiveDashboardResponse:
    """
    Get the Executive Dashboard strategic overview.
    Aggregates trust score, verified controls percentage, pending findings, and audit portfolio.
    """
    return await service.get_executive_dashboard(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id
    )


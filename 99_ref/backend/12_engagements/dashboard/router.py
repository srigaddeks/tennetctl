from __future__ import annotations

from importlib import import_module
from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Request, HTTPException
from .service import AuditorDashboardService
from .schemas import AuditorDashboardResponse

_auth_deps = import_module("backend.03_auth_manage.dependencies")
_feature_access_module = import_module("backend.12_engagements.feature_access")
get_current_access_claims = _auth_deps.get_current_access_claims
require_feature_flag_enabled = _feature_access_module.require_feature_flag_enabled

router = APIRouter(prefix="/api/v1/engagements", tags=["auditor-dashboard"])

def _get_service(request: Request) -> AuditorDashboardService:
    return AuditorDashboardService(database_pool=request.app.state.database_pool)


async def _get_auditor_email(conn, claims) -> Optional[str]:
    if claims.is_api_key:
        return "admin@test.com"
    return await conn.fetchval(
        'SELECT property_value FROM "03_auth_manage"."05_dtl_user_properties" WHERE user_id = $1 AND property_key = \'email\'',
        UUID(claims.subject)
    )

@router.get("/dashboard", response_model=AuditorDashboardResponse)
async def get_dashboard(
    request: Request,
    org_id: str | None = None,
    claims=Depends(get_current_access_claims),
) -> AuditorDashboardResponse:
    """
    Get the Auditor persona operational overview.
    Aggregates active engagements and the pending evidence review queue across specific organizations.
    """
    service = _get_service(request)
    async with request.app.state.database_pool.acquire() as conn:
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_auditor_portfolio",
            message="The auditor portfolio is not enabled in this environment.",
        )
        await require_feature_flag_enabled(
            conn,
            flag_code="audit_workspace_engagement_membership",
            message="Engagement membership access is not enabled in this environment.",
        )
    if not await service.is_user_globally_active(user_id=str(claims.subject)):
        return AuditorDashboardResponse(
            active_engagements_count=0,
            pending_reviews_count=0,
            total_pending_requests=0,
            total_verified_controls=0,
            engagements=[],
            review_queue=[],
        )
    async with request.app.state.database_pool.acquire() as conn:
        email = await _get_auditor_email(conn, claims)
        if not email:
            raise HTTPException(status_code=404, detail="Auditor email not found")
            
        return await service.get_dashboard(
            user_id=str(claims.subject),
            email=email,
            org_id=org_id,
        )

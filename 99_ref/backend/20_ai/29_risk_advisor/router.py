"""
FastAPI routes for the Risk Advisor agent.
Prefix: /api/v1/ai/risk-advisor

Routes:
  POST  /suggest-controls   Get AI-ranked control suggestions for a risk
  POST  /bulk-link          Enqueue bulk auto-link job for a framework
  GET   /jobs/{job_id}      Poll bulk-link job status
"""

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims

from .dependencies import get_risk_advisor_service
from .schemas import (
    BulkLinkJobResponse,
    BulkLinkRequest,
    JobStatusResponse,
    SuggestControlsRequest,
    SuggestControlsResponse,
)
from .service import RiskAdvisorService

router = InstrumentedAPIRouter(
    prefix="/api/v1/ai/risk-advisor",
    tags=["ai-risk-advisor"],
)


@router.post("/suggest-controls", response_model=SuggestControlsResponse)
async def suggest_controls(
    payload: SuggestControlsRequest,
    service: Annotated[RiskAdvisorService, Depends(get_risk_advisor_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> SuggestControlsResponse:
    """Return AI-ranked control suggestions for a risk."""
    return await service.suggest_controls(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


@router.post("/bulk-link", response_model=BulkLinkJobResponse, status_code=202)
async def bulk_link(
    payload: BulkLinkRequest,
    service: Annotated[RiskAdvisorService, Depends(get_risk_advisor_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> BulkLinkJobResponse:
    """Enqueue a background job to auto-link all controls in a framework to matching risks."""
    return await service.enqueue_bulk_link(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


@router.delete("/jobs")
async def delete_all_bulk_link_jobs(
    service: Annotated[RiskAdvisorService, Depends(get_risk_advisor_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> dict:
    """Delete ALL risk_advisor_bulk_link jobs for this tenant (admin cleanup)."""
    deleted = await service.delete_all_bulk_link_jobs(tenant_key=claims.tenant_key)
    return {"deleted": deleted}


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    service: Annotated[RiskAdvisorService, Depends(get_risk_advisor_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> JobStatusResponse:
    """Poll status of a bulk-link job."""
    return await service.get_job_status(
        job_id=job_id,
        tenant_key=claims.tenant_key,
    )

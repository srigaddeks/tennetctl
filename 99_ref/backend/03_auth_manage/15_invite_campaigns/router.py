from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request, status

from .dependencies import get_campaign_service
from .schemas import (
    BulkInviteRequest,
    BulkInviteResponse,
    CampaignListResponse,
    CampaignResponse,
    CreateCampaignRequest,
    UpdateCampaignRequest,
)
from .service import CampaignService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/am/campaigns", tags=["access-management"])


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    service: Annotated[CampaignService, Depends(get_campaign_service)],
    claims=Depends(get_current_access_claims),
    status_filter: str | None = Query(default=None, alias="status"),
    campaign_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> CampaignListResponse:
    return await service.list_campaigns(
        user_id=claims.subject,
        tenant_key=claims.tenant_key if hasattr(claims, "tenant_key") else "default",
        status=status_filter,
        campaign_type=campaign_type,
        limit=limit,
        offset=offset,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CampaignResponse)
async def create_campaign(
    payload: CreateCampaignRequest,
    request: Request,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
    claims=Depends(get_current_access_claims),
) -> CampaignResponse:
    return await service.create_campaign(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        payload=payload,
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
    claims=Depends(get_current_access_claims),
) -> CampaignResponse:
    return await service.get_campaign(user_id=claims.subject, campaign_id=campaign_id)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    payload: UpdateCampaignRequest,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
    claims=Depends(get_current_access_claims),
) -> CampaignResponse:
    return await service.update_campaign(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        campaign_id=campaign_id,
        payload=payload,
    )


@router.post("/{campaign_id}/bulk-invite", response_model=BulkInviteResponse)
async def bulk_invite(
    campaign_id: str,
    payload: BulkInviteRequest,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
    claims=Depends(get_current_access_claims),
) -> BulkInviteResponse:
    return await service.bulk_invite(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        campaign_id=campaign_id,
        payload=payload,
    )


@router.get("/{campaign_id}/invitations")
async def list_campaign_invitations(
    campaign_id: str,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
    claims=Depends(get_current_access_claims),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> dict:
    return await service.list_campaign_invitations(
        user_id=claims.subject,
        campaign_id=campaign_id,
        page=page,
        page_size=page_size,
    )

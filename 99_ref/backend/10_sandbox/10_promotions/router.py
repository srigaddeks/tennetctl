from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_promotion_service
from .schemas import (
    PromoteLibraryRequest,
    PromotePolicyRequest,
    PromoteSignalRequest,
    PromotionListResponse,
    PromotionResponse,
)
from .service import PromotionService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/promotions", tags=["sandbox-promotions"])


@router.post(
    "/signals/{signal_id}/promote",
    response_model=PromotionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def promote_signal(
    signal_id: str,
    body: PromoteSignalRequest,
    service: Annotated[PromotionService, Depends(get_promotion_service)],
    claims=Depends(get_current_access_claims),
) -> PromotionResponse:
    return await service.promote_signal(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        signal_id=signal_id,
        request=body,
    )


@router.post(
    "/policies/{policy_id}/promote",
    response_model=PromotionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def promote_policy(
    policy_id: str,
    body: PromotePolicyRequest,
    service: Annotated[PromotionService, Depends(get_promotion_service)],
    claims=Depends(get_current_access_claims),
) -> PromotionResponse:
    return await service.promote_policy(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        policy_id=policy_id,
        request=body,
    )


@router.post(
    "/libraries/{library_id}/promote",
    response_model=PromotionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def promote_library(
    library_id: str,
    body: PromoteLibraryRequest,
    service: Annotated[PromotionService, Depends(get_promotion_service)],
    claims=Depends(get_current_access_claims),
) -> PromotionResponse:
    return await service.promote_library(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        library_id=library_id,
        request=body,
    )


@router.get("", response_model=PromotionListResponse)
async def list_promotions(
    service: Annotated[PromotionService, Depends(get_promotion_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(default=None),
    signal_id: str | None = Query(default=None),
    policy_id: str | None = Query(default=None),
    library_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> PromotionListResponse:
    return await service.list_promotions(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        signal_id=signal_id,
        policy_id=policy_id,
        library_id=library_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{promotion_id}", response_model=PromotionResponse)
async def get_promotion(
    promotion_id: str,
    service: Annotated[PromotionService, Depends(get_promotion_service)],
    claims=Depends(get_current_access_claims),
) -> PromotionResponse:
    return await service.get_promotion_detail(
        user_id=claims.subject, promotion_id=promotion_id,
    )

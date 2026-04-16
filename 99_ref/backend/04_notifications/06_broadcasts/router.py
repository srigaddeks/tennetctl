from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_broadcast_service
from .service import BroadcastService
from ..schemas import BroadcastListResponse, BroadcastResponse, CreateBroadcastRequest

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/notifications", tags=["notification-broadcasts"])

# Org-scoped broadcast router — auth via org membership, not platform permission
org_router = InstrumentedAPIRouter(prefix="/api/v1/am/orgs", tags=["org-broadcasts"])


@router.get("/broadcasts", response_model=BroadcastListResponse)
async def list_broadcasts(
    service: Annotated[BroadcastService, Depends(get_broadcast_service)],
    claims=Depends(get_current_access_claims),
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> BroadcastListResponse:
    return await service.list_broadcasts(
        user_id=claims.subject, tenant_key=claims.tenant_key, limit=limit, offset=offset
    )


@router.post(
    "/broadcasts",
    response_model=BroadcastResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_broadcast(
    body: CreateBroadcastRequest,
    service: Annotated[BroadcastService, Depends(get_broadcast_service)],
    claims=Depends(get_current_access_claims),
) -> BroadcastResponse:
    return await service.create_broadcast(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


@router.post(
    "/broadcasts/{broadcast_id}/send",
    response_model=BroadcastResponse,
)
async def send_broadcast(
    broadcast_id: str,
    service: Annotated[BroadcastService, Depends(get_broadcast_service)],
    claims=Depends(get_current_access_claims),
) -> BroadcastResponse:
    return await service.send_broadcast(
        user_id=claims.subject, broadcast_id=broadcast_id
    )


# ---------------------------------------------------------------------------
# Org-scoped broadcast endpoints
# Auth: org membership (any active member can view; create/send requires view only)
# ---------------------------------------------------------------------------

@org_router.get("/{org_id}/broadcasts", response_model=list[BroadcastResponse])
async def list_org_broadcasts(
    org_id: str,
    service: Annotated[BroadcastService, Depends(get_broadcast_service)],
    claims=Depends(get_current_access_claims),
) -> list[BroadcastResponse]:
    return await service.list_org_broadcasts(
        user_id=claims.subject, org_id=org_id, tenant_key=claims.tenant_key
    )


@org_router.post(
    "/{org_id}/broadcasts",
    response_model=BroadcastResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_org_broadcast(
    org_id: str,
    body: CreateBroadcastRequest,
    service: Annotated[BroadcastService, Depends(get_broadcast_service)],
    claims=Depends(get_current_access_claims),
) -> BroadcastResponse:
    return await service.create_org_broadcast(
        user_id=claims.subject, org_id=org_id, tenant_key=claims.tenant_key, request=body
    )


@org_router.post("/{org_id}/broadcasts/{broadcast_id}/send", response_model=BroadcastResponse)
async def send_org_broadcast(
    org_id: str,
    broadcast_id: str,
    service: Annotated[BroadcastService, Depends(get_broadcast_service)],
    claims=Depends(get_current_access_claims),
) -> BroadcastResponse:
    return await service.send_org_broadcast(
        user_id=claims.subject, org_id=org_id, broadcast_id=broadcast_id
    )

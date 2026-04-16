"""FastAPI router for global library endpoints."""

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_global_library_service
from .schemas import (
    GlobalLibraryListResponse,
    GlobalLibraryResponse,
    PublishGlobalLibraryRequest,
    SubscribeRequest,
    SubscriptionListResponse,
    SubscriptionResponse,
)
from .service import GlobalLibraryService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/global-libraries", tags=["sandbox-global-library"])


@router.get("", response_model=GlobalLibraryListResponse)
async def list_global_libraries(
    service: Annotated[GlobalLibraryService, Depends(get_global_library_service)],
    claims=Depends(get_current_access_claims),
    category_code: str | None = Query(default=None),
    connector_type_code: str | None = Query(default=None),
    is_featured: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> GlobalLibraryListResponse:
    return await service.list_global_libraries(
        user_id=claims.subject,
        category_code=category_code,
        connector_type_code=connector_type_code,
        is_featured=is_featured,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=GlobalLibraryResponse, status_code=status.HTTP_201_CREATED)
async def publish_global_library(
    body: PublishGlobalLibraryRequest,
    service: Annotated[GlobalLibraryService, Depends(get_global_library_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> GlobalLibraryResponse:
    """Publish an org library to the global catalog (platform admin only)."""
    return await service.publish_global_library(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=body,
    )


@router.post("/{global_library_id}/subscribe", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe(
    global_library_id: str,
    body: SubscribeRequest,
    service: Annotated[GlobalLibraryService, Depends(get_global_library_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str = Query(...),
) -> SubscriptionResponse:
    """Subscribe an org to a global library — clones all signals, threats, policies locally."""
    return await service.subscribe(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        global_library_id=global_library_id,
        request=body,
    )


@router.get("/subscriptions", response_model=SubscriptionListResponse)
async def list_subscriptions(
    service: Annotated[GlobalLibraryService, Depends(get_global_library_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> SubscriptionListResponse:
    """List the org's subscriptions with update availability."""
    return await service.list_subscriptions(
        user_id=claims.subject,
        org_id=org_id,
    )

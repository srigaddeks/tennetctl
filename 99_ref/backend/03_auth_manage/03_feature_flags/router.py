from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Request, status

from .dependencies import get_feature_flag_service
from .schemas import (
    AddPermissionRequest,
    CreateFeatureCategoryRequest,
    CreateFeatureFlagRequest,
    FeatureCategoryResponse,
    FeatureFlagListResponse,
    FeatureFlagResponse,
    FeaturePermissionResponse,
    OrgAvailableFlagsResponse,
    PermissionActionListResponse,
    PermissionActionTypeResponse,
    UpdateFeatureFlagRequest,
)
from .service import FeatureFlagService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/am/features", tags=["access-management"])


@router.get("", response_model=FeatureFlagListResponse)
async def list_feature_flags(
    service: Annotated[FeatureFlagService, Depends(get_feature_flag_service)],
    claims=Depends(get_current_access_claims),
) -> FeatureFlagListResponse:
    return await service.list_flags(actor_id=claims.subject)


@router.get("/org-available", response_model=OrgAvailableFlagsResponse)
async def list_org_available_flags(
    service: Annotated[FeatureFlagService, Depends(get_feature_flag_service)],
    claims=Depends(get_current_access_claims),
) -> OrgAvailableFlagsResponse:
    """List org-scoped feature flags visible to org admins.

    No platform-level permission required — any authenticated user can call this.
    Returns only flags where org_visibility is 'locked' or 'unlocked' (hidden flags are excluded).
    """
    return await service.list_org_available_flags()


@router.get("/permission-actions", response_model=PermissionActionListResponse)
async def list_permission_actions(
    service: Annotated[FeatureFlagService, Depends(get_feature_flag_service)],
    claims=Depends(get_current_access_claims),
) -> PermissionActionListResponse:
    return await service.list_permission_actions(actor_id=claims.subject)


@router.post("/categories", status_code=status.HTTP_201_CREATED, response_model=FeatureCategoryResponse)
async def create_feature_category(
    payload: CreateFeatureCategoryRequest,
    service: Annotated[FeatureFlagService, Depends(get_feature_flag_service)],
    claims=Depends(get_current_access_claims),
) -> FeatureCategoryResponse:
    return await service.create_category(payload, actor_id=claims.subject)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=FeatureFlagResponse)
async def create_feature_flag(
    payload: CreateFeatureFlagRequest,
    request: Request,
    service: Annotated[FeatureFlagService, Depends(get_feature_flag_service)],
    claims=Depends(get_current_access_claims),
) -> FeatureFlagResponse:
    return await service.create_flag(
        payload,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/{code}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    code: str,
    payload: UpdateFeatureFlagRequest,
    request: Request,
    service: Annotated[FeatureFlagService, Depends(get_feature_flag_service)],
    claims=Depends(get_current_access_claims),
) -> FeatureFlagResponse:
    return await service.update_flag(
        code,
        payload,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/action-types", response_model=list[PermissionActionTypeResponse])
async def list_action_types(
    service: Annotated[FeatureFlagService, Depends(get_feature_flag_service)],
    claims=Depends(get_current_access_claims),
) -> list[PermissionActionTypeResponse]:
    """List all available permission action types (view, create, update, etc.)."""
    return await service.list_action_types()


@router.post(
    "/{code}/permissions",
    status_code=status.HTTP_201_CREATED,
    response_model=FeaturePermissionResponse,
)
async def add_permission_to_flag(
    code: str,
    payload: AddPermissionRequest,
    service: Annotated[FeatureFlagService, Depends(get_feature_flag_service)],
    claims=Depends(get_current_access_claims),
) -> FeaturePermissionResponse:
    """Add a permission (action) to a feature flag."""
    return await service.add_permission(code, payload, actor_id=claims.subject)


@router.delete(
    "/{code}/permissions/{action_code}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_permission_from_flag(
    code: str,
    action_code: str,
    service: Annotated[FeatureFlagService, Depends(get_feature_flag_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Remove a permission from a feature flag."""
    await service.remove_permission(code, action_code, actor_id=claims.subject)



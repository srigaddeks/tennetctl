from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_version_service
from .schemas import (
    CreateVersionRequest,
    VersionListResponse,
    VersionResponse,
)
from .service import VersionService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/fr", tags=["grc-versions"])


@router.post(
    "/frameworks/{framework_id}/auto-version",
    response_model=VersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_auto_version(
    framework_id: str,
    service: Annotated[VersionService, Depends(get_version_service)],
    claims=Depends(get_current_access_claims),
    change_type: str = Query(...),
    change_summary: str | None = Query(None),
) -> VersionResponse:
    """Create a new draft version automatically when framework content changes.

    Only creates a version if the framework is approved and no draft version exists.
    """
    return await service.create_auto_version(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        change_type=change_type,
        change_summary=change_summary,
    )


@router.get("/frameworks/{framework_id}/versions", response_model=VersionListResponse)
async def list_versions(
    framework_id: str,
    service: Annotated[VersionService, Depends(get_version_service)],
    claims=Depends(get_current_access_claims),
    scope_org_id: str | None = Query(None),
    scope_workspace_id: str | None = Query(None),
) -> VersionListResponse:
    return await service.list_versions(
        user_id=claims.subject,
        framework_id=framework_id,
        scope_org_id=scope_org_id,
        scope_workspace_id=scope_workspace_id,
    )


@router.get(
    "/frameworks/{framework_id}/versions/{version_id}", response_model=VersionResponse
)
async def get_version(
    framework_id: str,
    version_id: str,
    service: Annotated[VersionService, Depends(get_version_service)],
    claims=Depends(get_current_access_claims),
    scope_org_id: str | None = Query(None),
    scope_workspace_id: str | None = Query(None),
) -> VersionResponse:
    return await service.get_version(
        user_id=claims.subject,
        framework_id=framework_id,
        version_id=version_id,
        scope_org_id=scope_org_id,
        scope_workspace_id=scope_workspace_id,
    )


@router.post(
    "/frameworks/{framework_id}/versions",
    response_model=VersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_version(
    framework_id: str,
    body: CreateVersionRequest,
    service: Annotated[VersionService, Depends(get_version_service)],
    claims=Depends(get_current_access_claims),
) -> VersionResponse:
    return await service.create_version(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        request=body,
    )


@router.post(
    "/frameworks/{framework_id}/versions/{version_id}/publish",
    response_model=VersionResponse,
)
async def publish_version(
    framework_id: str,
    version_id: str,
    service: Annotated[VersionService, Depends(get_version_service)],
    claims=Depends(get_current_access_claims),
) -> VersionResponse:
    return await service.publish_version(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        version_id=version_id,
    )


@router.post(
    "/frameworks/{framework_id}/versions/{version_id}/deprecate",
    response_model=VersionResponse,
)
async def deprecate_version(
    framework_id: str,
    version_id: str,
    service: Annotated[VersionService, Depends(get_version_service)],
    claims=Depends(get_current_access_claims),
) -> VersionResponse:
    return await service.deprecate_version(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        version_id=version_id,
    )


@router.post(
    "/frameworks/{framework_id}/versions/{version_id}/restore",
    response_model=VersionResponse,
)
async def restore_version(
    framework_id: str,
    version_id: str,
    service: Annotated[VersionService, Depends(get_version_service)],
    claims=Depends(get_current_access_claims),
) -> VersionResponse:
    """Restore a previous version by creating a new published version copied from it."""
    return await service.restore_version(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        version_id=version_id,
    )

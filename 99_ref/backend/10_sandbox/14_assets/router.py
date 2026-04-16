from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_asset_service
from .schemas import (
    AssetAccessGrantRequest,
    AssetAccessGrantResponse,
    AssetChangeEntry,
    AssetListResponse,
    AssetPropertyResponse,
    AssetResponse,
    AssetSnapshotResponse,
    AssetStatsResponse,
)
from .service import AssetService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/assets", tags=["assets"])


@router.get("", response_model=AssetListResponse)
async def list_assets(
    service: Annotated[AssetService, Depends(get_asset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    connector_id: str | None = Query(default=None),
    asset_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
) -> AssetListResponse:
    return await service.list_assets(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        connector_id=connector_id,
        asset_type=asset_type,
        status=status,
        offset=offset,
        limit=limit,
        user_group_ids=None,
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    service: Annotated[AssetService, Depends(get_asset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> AssetResponse:
    return await service.get_asset_with_access_check(
        user_id=claims.subject,
        asset_id=asset_id,
        org_id=org_id,
        user_group_ids=None,
    )


@router.get("/{asset_id}/properties", response_model=list[AssetPropertyResponse])
async def get_asset_properties(
    asset_id: str,
    service: Annotated[AssetService, Depends(get_asset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> list[AssetPropertyResponse]:
    return await service.get_asset_properties(
        user_id=claims.subject,
        asset_id=asset_id,
        org_id=org_id,
    )


@router.get("/{asset_id}/snapshots", response_model=list[AssetSnapshotResponse])
async def get_asset_snapshots(
    asset_id: str,
    service: Annotated[AssetService, Depends(get_asset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> list[AssetSnapshotResponse]:
    return await service.get_asset_snapshots(
        user_id=claims.subject,
        asset_id=asset_id,
        org_id=org_id,
    )


@router.get("/{asset_id}/changes", response_model=list[AssetChangeEntry])
async def get_asset_changes(
    asset_id: str,
    service: Annotated[AssetService, Depends(get_asset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> list[AssetChangeEntry]:
    return await service.get_asset_changes(
        user_id=claims.subject,
        asset_id=asset_id,
        org_id=org_id,
    )


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_asset(
    asset_id: str,
    service: Annotated[AssetService, Depends(get_asset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    await service.soft_delete_asset(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        asset_id=asset_id,
        org_id=org_id,
        deleted_by=claims.subject,
        user_group_ids=None,
    )


@router.get("/{asset_id}/access", response_model=list[AssetAccessGrantResponse])
async def list_access_grants(
    asset_id: str,
    service: Annotated[AssetService, Depends(get_asset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> list[AssetAccessGrantResponse]:
    return await service.list_access_grants(
        user_id=claims.subject,
        asset_id=asset_id,
        org_id=org_id,
    )


@router.post(
    "/{asset_id}/access",
    response_model=AssetAccessGrantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def grant_access(
    asset_id: str,
    body: AssetAccessGrantRequest,
    service: Annotated[AssetService, Depends(get_asset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> AssetAccessGrantResponse:
    return await service.grant_access(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        asset_id=asset_id,
        org_id=org_id,
        user_group_id=body.user_group_id,
        role_code=body.role_code,
        granted_by=claims.subject,
    )


@router.delete("/{asset_id}/access/{grant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_access(
    asset_id: str,
    grant_id: str,
    service: Annotated[AssetService, Depends(get_asset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    await service.revoke_access(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        grant_id=grant_id,
        asset_id=asset_id,
        org_id=org_id,
        revoked_by=claims.subject,
    )


@router.get("/stats", response_model=AssetStatsResponse)
async def get_stats(
    service: Annotated[AssetService, Depends(get_asset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> AssetStatsResponse:
    """Dashboard summary: asset counts by type and status, connector health."""
    return await service.get_stats(user_id=claims.subject, org_id=org_id)

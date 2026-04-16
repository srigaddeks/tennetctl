from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_asset_connector_service
from .schemas import (
    AssetConnectorListResponse,
    AssetConnectorResponse,
    CreateAssetConnectorRequest,
    TestConnectionResponse,
    UpdateAssetConnectorRequest,
)
from .service import AssetConnectorService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(
    prefix="/api/v1/sb/asset-connectors",
    tags=["asset-connectors"],
)


@router.get("", response_model=AssetConnectorListResponse)
async def list_connectors(
    service: Annotated[AssetConnectorService, Depends(get_asset_connector_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    provider_code: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> AssetConnectorListResponse:
    return await service.list_connectors(
        user_id=claims.subject,
        org_id=org_id,
        provider_code=provider_code,
        offset=offset,
        limit=limit,
    )


@router.post("", response_model=AssetConnectorResponse, status_code=status.HTTP_201_CREATED)
async def create_connector(
    body: CreateAssetConnectorRequest,
    service: Annotated[AssetConnectorService, Depends(get_asset_connector_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> AssetConnectorResponse:
    return await service.create_connector(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        body=body,
    )


@router.get("/{connector_id}", response_model=AssetConnectorResponse)
async def get_connector(
    connector_id: str,
    service: Annotated[AssetConnectorService, Depends(get_asset_connector_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> AssetConnectorResponse:
    return await service.get_connector(
        user_id=claims.subject,
        connector_id=connector_id,
        org_id=org_id,
    )


@router.patch("/{connector_id}", response_model=AssetConnectorResponse)
async def update_connector(
    connector_id: str,
    body: UpdateAssetConnectorRequest,
    service: Annotated[AssetConnectorService, Depends(get_asset_connector_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> AssetConnectorResponse:
    return await service.update_connector(
        user_id=claims.subject,
        connector_id=connector_id,
        org_id=org_id,
        tenant_key=claims.tenant_key,
        body=body,
    )


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(
    connector_id: str,
    service: Annotated[AssetConnectorService, Depends(get_asset_connector_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    await service.delete_connector(
        user_id=claims.subject,
        connector_id=connector_id,
        org_id=org_id,
        tenant_key=claims.tenant_key,
    )


@router.post("/{connector_id}/test", response_model=TestConnectionResponse)
async def test_connection(
    connector_id: str,
    service: Annotated[AssetConnectorService, Depends(get_asset_connector_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> TestConnectionResponse:
    """Test the live connection for this connector. Updates health_status."""
    return await service.test_connection(
        user_id=claims.subject,
        connector_id=connector_id,
        org_id=org_id,
        tenant_key=claims.tenant_key,
    )

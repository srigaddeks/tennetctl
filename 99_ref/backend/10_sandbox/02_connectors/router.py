from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_connector_service
from .schemas import (
    ConnectorListResponse,
    ConnectorResponse,
    CreateConnectorRequest,
    PreflightTestRequest,
    TestConnectionResponse,
    UpdateConnectorRequest,
    UpdateCredentialsRequest,
)
from .service import ConnectorService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/connectors", tags=["sandbox-connectors"])


@router.get("", response_model=ConnectorListResponse)
async def list_connectors(
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str | None = Query(default=None),
    connector_type_code: str | None = Query(default=None),
    category_code: str | None = Query(default=None),
    health_status: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> ConnectorListResponse:
    return await service.list_connectors(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        connector_type_code=connector_type_code,
        category_code=category_code,
        health_status=health_status,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.get("/{connector_id}", response_model=ConnectorResponse)
async def get_connector(
    connector_id: str,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    claims=Depends(get_current_access_claims),
) -> ConnectorResponse:
    return await service.get_connector(
        user_id=claims.subject, connector_id=connector_id
    )


@router.get("/{connector_id}/properties", response_model=dict[str, str])
async def get_connector_properties(
    connector_id: str,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    claims=Depends(get_current_access_claims),
) -> dict[str, str]:
    return await service.get_connector_properties(
        user_id=claims.subject, connector_id=connector_id
    )


@router.post("", response_model=ConnectorResponse, status_code=status.HTTP_201_CREATED)
async def create_connector(
    body: CreateConnectorRequest,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> ConnectorResponse:
    return await service.create_connector(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=body,
    )


@router.patch("/{connector_id}", response_model=ConnectorResponse)
async def update_connector(
    connector_id: str,
    body: UpdateConnectorRequest,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> ConnectorResponse:
    return await service.update_connector(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        connector_id=connector_id,
        request=body,
    )


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connector(
    connector_id: str,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    await service.delete_connector(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        connector_id=connector_id,
    )


@router.patch("/{connector_id}/credentials", status_code=status.HTTP_204_NO_CONTENT)
async def update_credentials(
    connector_id: str,
    body: UpdateCredentialsRequest,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    await service.update_credentials(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        connector_id=connector_id,
        request=body,
    )


@router.post("/preflight-test", response_model=TestConnectionResponse)
async def preflight_test(
    body: PreflightTestRequest,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    claims=Depends(get_current_access_claims),
) -> TestConnectionResponse:
    """Test a connection before saving. Stateless — nothing is persisted."""
    return await service.preflight_test(
        user_id=claims.subject,
        request=body,
    )


@router.post("/{connector_id}/test", response_model=TestConnectionResponse)
async def test_connection(
    connector_id: str,
    service: Annotated[ConnectorService, Depends(get_connector_service)],
    claims=Depends(get_current_access_claims),
) -> TestConnectionResponse:
    return await service.test_connection(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        connector_id=connector_id,
    )

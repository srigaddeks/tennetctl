from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_collection_run_service
from .schemas import (
    CollectionRunListResponse,
    CollectionRunResponse,
    TriggerCollectionRequest,
)
from .service import CollectionRunService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb", tags=["collection-runs"])


@router.get("/collection-runs", response_model=CollectionRunListResponse)
async def list_runs(
    service: Annotated[CollectionRunService, Depends(get_collection_run_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    connector_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
) -> CollectionRunListResponse:
    return await service.list_runs(
        user_id=claims.subject,
        org_id=org_id,
        connector_id=connector_id,
        status=status,
        offset=offset,
        limit=limit,
    )


@router.get("/collection-runs/{run_id}", response_model=CollectionRunResponse)
async def get_run(
    run_id: str,
    service: Annotated[CollectionRunService, Depends(get_collection_run_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> CollectionRunResponse:
    return await service.get_run(
        user_id=claims.subject,
        run_id=run_id,
        org_id=org_id,
    )


@router.post(
    "/connectors/{connector_id}/collect",
    response_model=CollectionRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_collection(
    connector_id: str,
    body: TriggerCollectionRequest,
    service: Annotated[CollectionRunService, Depends(get_collection_run_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> CollectionRunResponse:
    return await service.trigger_collection(
        user_id=claims.subject,
        connector_instance_id=connector_id,
        org_id=org_id,
        tenant_key=claims.tenant_key,
        triggered_by=claims.subject,
        asset_types=body.asset_types,
    )


@router.get("/collection-runs/{run_id}/snapshots")
async def list_run_snapshots(
    run_id: str,
    service: Annotated[CollectionRunService, Depends(get_collection_run_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    asset_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return await service.list_run_snapshots(
        user_id=claims.subject,
        run_id=run_id,
        org_id=org_id,
        asset_type=asset_type,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/collection-runs/{run_id}/cancel",
    response_model=CollectionRunResponse,
)
async def cancel_run(
    run_id: str,
    service: Annotated[CollectionRunService, Depends(get_collection_run_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> CollectionRunResponse:
    return await service.cancel_run(
        user_id=claims.subject,
        run_id=run_id,
        org_id=org_id,
    )

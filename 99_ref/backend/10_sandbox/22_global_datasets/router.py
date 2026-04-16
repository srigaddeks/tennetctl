from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_global_dataset_service
from .schemas import (
    GlobalDatasetListResponse,
    GlobalDatasetResponse,
    GlobalDatasetStatsResponse,
    GlobalDatasetVersionListResponse,
    PublishGlobalDatasetRequest,
    PullGlobalDatasetRequest,
    PullResultResponse,
    UpdateGlobalDatasetRequest,
)
from .service import GlobalDatasetService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/global-datasets", tags=["sandbox-global-datasets"])


# ── publish ──────────────────────────────────────────────────────────────────

@router.post("/publish", response_model=GlobalDatasetResponse, status_code=status.HTTP_201_CREATED)
async def publish_global_dataset(
    body: PublishGlobalDatasetRequest,
    service: Annotated[GlobalDatasetService, Depends(get_global_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
):
    return await service.publish_dataset(
        request=body,
        org_id=org_id,
        user_id=claims.subject,
    )


# ── list ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=GlobalDatasetListResponse)
async def list_global_datasets(
    service: Annotated[GlobalDatasetService, Depends(get_global_dataset_service)],
    claims=Depends(get_current_access_claims),
    connector_type_code: str | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(None),
    publish_status: str | None = Query(None),
    is_featured: bool | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return await service.list_datasets(
        connector_type_code=connector_type_code,
        category=category,
        search=search,
        publish_status=publish_status,
        is_featured=is_featured,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


# ── stats ────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=GlobalDatasetStatsResponse)
async def get_global_dataset_stats(
    service: Annotated[GlobalDatasetService, Depends(get_global_dataset_service)],
    claims=Depends(get_current_access_claims),
):
    return await service.get_stats()


# ── get ──────────────────────────────────────────────────────────────────────

@router.get("/{dataset_id}", response_model=GlobalDatasetResponse)
async def get_global_dataset(
    dataset_id: str,
    service: Annotated[GlobalDatasetService, Depends(get_global_dataset_service)],
    claims=Depends(get_current_access_claims),
):
    return await service.get_dataset(dataset_id)


# ── versions ─────────────────────────────────────────────────────────────────

@router.get("/{dataset_id}/versions", response_model=GlobalDatasetVersionListResponse)
async def list_global_dataset_versions(
    dataset_id: str,
    service: Annotated[GlobalDatasetService, Depends(get_global_dataset_service)],
    claims=Depends(get_current_access_claims),
):
    return await service.list_versions(dataset_id)


# ── update ───────────────────────────────────────────────────────────────────

@router.patch("/{dataset_id}", response_model=GlobalDatasetResponse)
async def update_global_dataset(
    dataset_id: str,
    body: UpdateGlobalDatasetRequest,
    service: Annotated[GlobalDatasetService, Depends(get_global_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
):
    return await service.update_dataset(dataset_id, body, user_id=claims.subject, org_id=org_id)


# ── deprecate ────────────────────────────────────────────────────────────────

@router.post("/{dataset_id}/deprecate", response_model=GlobalDatasetResponse)
async def deprecate_global_dataset(
    dataset_id: str,
    service: Annotated[GlobalDatasetService, Depends(get_global_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
):
    return await service.deprecate_dataset(dataset_id, user_id=claims.subject, org_id=org_id)


# ── pull ─────────────────────────────────────────────────────────────────────

@router.post("/{dataset_id}/pull", response_model=PullResultResponse, status_code=status.HTTP_201_CREATED)
async def pull_global_dataset(
    dataset_id: str,
    body: PullGlobalDatasetRequest,
    service: Annotated[GlobalDatasetService, Depends(get_global_dataset_service)],
    claims=Depends(get_current_access_claims),
):
    return await service.pull_dataset(
        dataset_id=dataset_id,
        org_id=body.org_id,
        workspace_id=body.workspace_id,
        connector_instance_id=body.connector_instance_id,
        custom_dataset_code=body.custom_dataset_code,
        user_id=claims.subject,
    )

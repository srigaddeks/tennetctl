from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_global_control_test_service
from .schemas import (
    DeployControlTestRequest,
    DeployResultResponse,
    GlobalControlTestListResponse,
    GlobalControlTestResponse,
    GlobalControlTestStatsResponse,
    PublishGlobalControlTestRequest,
    UpdateGlobalControlTestRequest,
)
from .service import GlobalControlTestService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/global-tests", tags=["sandbox-global-control-tests"])


@router.post("/publish", response_model=GlobalControlTestResponse, status_code=status.HTTP_201_CREATED)
async def publish_global_control_test(
    body: PublishGlobalControlTestRequest,
    service: Annotated[GlobalControlTestService, Depends(get_global_control_test_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
):
    return await service.publish_control_test(request=body, org_id=org_id, user_id=claims.subject)


@router.get("", response_model=GlobalControlTestListResponse)
async def list_global_control_tests(
    service: Annotated[GlobalControlTestService, Depends(get_global_control_test_service)],
    claims=Depends(get_current_access_claims),
    connector_type_code: str | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(None),
    linked_dataset_code: str | None = Query(None),
    publish_status: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return await service.list_tests(
        connector_type_code=connector_type_code,
        category=category,
        search=search,
        linked_dataset_code=linked_dataset_code,
        publish_status=publish_status,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=GlobalControlTestStatsResponse)
async def get_global_control_test_stats(
    service: Annotated[GlobalControlTestService, Depends(get_global_control_test_service)],
    claims=Depends(get_current_access_claims),
):
    return await service.get_stats()


@router.get("/deployed-ids")
async def list_deployed_ids(
    service: Annotated[GlobalControlTestService, Depends(get_global_control_test_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str | None = Query(default=None),
) -> list[str]:
    """Return global test IDs already deployed to this org/workspace."""
    return await service.list_deployed_ids(org_id=org_id, workspace_id=workspace_id)


@router.get("/{test_id}", response_model=GlobalControlTestResponse)
async def get_global_control_test(
    test_id: str,
    service: Annotated[GlobalControlTestService, Depends(get_global_control_test_service)],
    claims=Depends(get_current_access_claims),
):
    return await service.get_test(test_id)


@router.patch("/{test_id}", response_model=GlobalControlTestResponse)
async def update_global_control_test(
    test_id: str,
    body: UpdateGlobalControlTestRequest,
    service: Annotated[GlobalControlTestService, Depends(get_global_control_test_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
):
    return await service.update_test(test_id, body, user_id=claims.subject, org_id=org_id)


@router.post("/{test_id}/deprecate", response_model=GlobalControlTestResponse)
async def deprecate_global_control_test(
    test_id: str,
    service: Annotated[GlobalControlTestService, Depends(get_global_control_test_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
):
    return await service.deprecate_test(test_id, user_id=claims.subject, org_id=org_id)


@router.post("/{test_id}/deploy", response_model=DeployResultResponse, status_code=status.HTTP_201_CREATED)
async def deploy_global_control_test(
    test_id: str,
    body: DeployControlTestRequest,
    service: Annotated[GlobalControlTestService, Depends(get_global_control_test_service)],
    claims=Depends(get_current_access_claims),
):
    return await service.deploy_to_workspace(
        test_id=test_id,
        org_id=body.org_id,
        workspace_id=body.workspace_id,
        connector_instance_id=body.connector_instance_id,
        user_id=claims.subject,
    )

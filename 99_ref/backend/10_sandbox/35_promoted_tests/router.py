from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from fastapi import Request

from .dependencies import get_promoted_test_service
from .schemas import (
    ExecutePromotedTestRequest,
    ExecutePromotedTestResponse,
    PromotedTestListResponse,
    PromotedTestResponse,
    UpdatePromotedTestRequest,
)
from .service import PromotedTestService
from .dashboard import MonitoringDashboardResponse, get_monitoring_dashboard

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(
    prefix="/api/v1/sb/promoted-tests", tags=["sandbox-promoted-tests"]
)


@router.get("/dashboard", response_model=MonitoringDashboardResponse)
async def get_dashboard(
    request: Request,
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str | None = Query(default=None),
) -> MonitoringDashboardResponse:
    pool = request.app.state.database_pool
    return await get_monitoring_dashboard(pool, org_id, workspace_id=workspace_id)


@router.get("", response_model=PromotedTestListResponse)
async def list_promoted_tests(
    service: Annotated[PromotedTestService, Depends(get_promoted_test_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    linked_asset_id: str | None = Query(default=None),
    is_active: bool | None = Query(default=True),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> PromotedTestListResponse:
    return await service.list_tests(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        search=search,
        linked_asset_id=linked_asset_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.get("/{test_id}", response_model=PromotedTestResponse)
async def get_promoted_test(
    test_id: str,
    service: Annotated[PromotedTestService, Depends(get_promoted_test_service)],
    claims=Depends(get_current_access_claims),
) -> PromotedTestResponse:
    return await service.get_test(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        test_id=test_id,
    )


@router.get("/{test_id}/history", response_model=PromotedTestListResponse)
async def get_promoted_test_history(
    test_id: str,
    service: Annotated[PromotedTestService, Depends(get_promoted_test_service)],
    claims=Depends(get_current_access_claims),
) -> PromotedTestListResponse:
    return await service.get_version_history(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        test_id=test_id,
    )


@router.patch("/{test_id}", response_model=PromotedTestResponse)
async def update_promoted_test(
    test_id: str,
    body: UpdatePromotedTestRequest,
    service: Annotated[PromotedTestService, Depends(get_promoted_test_service)],
    claims=Depends(get_current_access_claims),
) -> PromotedTestResponse:
    return await service.update_test(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        test_id=test_id,
        request=body,
    )


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_promoted_test(
    test_id: str,
    service: Annotated[PromotedTestService, Depends(get_promoted_test_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_test(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        test_id=test_id,
    )


@router.post("/{test_id}/execute", response_model=ExecutePromotedTestResponse)
async def execute_promoted_test(
    test_id: str,
    body: ExecutePromotedTestRequest,
    service: Annotated[PromotedTestService, Depends(get_promoted_test_service)],
    claims=Depends(get_current_access_claims),
) -> ExecutePromotedTestResponse:
    return await service.execute_test(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        test_id=test_id,
        dataset_id=body.dataset_id,
    )

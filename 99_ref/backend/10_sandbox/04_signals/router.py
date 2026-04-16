from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

from .dependencies import get_signal_service
from .schemas import (
    BulkImportRequest,
    BulkImportResponse,
    CreateSignalRequest,
    ExecuteLiveRequest,
    ExecuteLiveResponse,
    ExecuteSignalRequest,
    ExecuteSignalResponse,
    GenerateSignalRequest,
    GenerateSignalResponse,
    SignalListResponse,
    SignalResponse,
    SignalVersionResponse,
    TestSuiteResponse,
    UpdateSignalRequest,
    ValidateSignalRequest,
)
from .service import SignalService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/signals", tags=["sandbox-signals"])


@router.get("", response_model=SignalListResponse)
async def list_signals(
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
    workspace_id: str | None = Query(None, description="Filter by workspace"),
    signal_status_code: str | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search by name or code"),
    sort_by: str = Query("created_at", description="Sort column"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> SignalListResponse:
    return await service.list_signals(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        signal_status_code=signal_status_code,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: str,
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
) -> SignalResponse:
    return await service.get_signal(user_id=claims.subject, signal_id=signal_id)


@router.post("", response_model=SignalResponse, status_code=201)
async def create_signal(
    request: CreateSignalRequest,
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
    workspace_id: str | None = Query(None, description="Workspace ID"),
) -> SignalResponse:
    if workspace_id and not request.workspace_id:
        request = request.model_copy(update={"workspace_id": workspace_id})
    return await service.create_signal(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=request,
    )


@router.patch("/{signal_id}", response_model=SignalResponse)
async def update_signal(
    signal_id: str,
    request: UpdateSignalRequest,
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> SignalResponse:
    return await service.update_signal(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        signal_id=signal_id,
        request=request,
    )


@router.delete("/{signal_id}", status_code=204)
async def delete_signal(
    signal_id: str,
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> None:
    await service.delete_signal(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        signal_id=signal_id,
    )


@router.post("/bulk-import", response_model=BulkImportResponse, status_code=201)
async def bulk_import(
    body: BulkImportRequest,
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> BulkImportResponse:
    """Bulk-create or update signals from a list of definitions."""
    result = await service.bulk_import(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=body.workspace_id,
        signals=[s.model_dump() for s in body.signals],
    )
    return BulkImportResponse(**result)


@router.post("/generate", response_model=GenerateSignalResponse)
async def generate_signal(
    request: GenerateSignalRequest,
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
) -> GenerateSignalResponse:
    return await service.generate_signal(user_id=claims.subject, request=request)


@router.post("/{signal_id}/validate", response_model=SignalResponse)
async def validate_signal(
    signal_id: str,
    _body: ValidateSignalRequest,
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
) -> SignalResponse:
    return await service.validate_signal(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        signal_id=signal_id,
    )


@router.get("/{signal_id}/versions", response_model=list[SignalVersionResponse])
async def list_signal_versions(
    signal_id: str,
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> list[SignalVersionResponse]:
    return await service.list_versions(
        user_id=claims.subject,
        org_id=org_id,
        signal_id=signal_id,
    )


@router.post("/{signal_id}/execute", response_model=ExecuteSignalResponse)
async def execute_signal(
    signal_id: str,
    request: ExecuteSignalRequest,
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> ExecuteSignalResponse:
    result = await service.execute_signal(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        signal_id=signal_id,
        dataset=request.dataset,
        configurable_args=request.configurable_args,
    )
    return ExecuteSignalResponse(**result)


@router.get("/{signal_id}/runs")
async def list_signal_runs(
    signal_id: str,
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
) -> dict:
    return await service.list_runs(user_id=claims.subject, signal_id=signal_id)


@router.post("/{signal_id}/test-suite", response_model=TestSuiteResponse)
async def run_test_suite(
    signal_id: str,
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
    test_dataset_id: str | None = Query(
        None, description="Optional test dataset override"
    ),
) -> TestSuiteResponse:
    """Run the signal's test suite comparing actual vs expected outputs."""
    return await service.run_test_suite(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        signal_id=signal_id,
        test_dataset_id=test_dataset_id,
    )


@router.post("/{signal_id}/execute-live", response_model=ExecuteLiveResponse)
async def execute_live(
    signal_id: str,
    body: ExecuteLiveRequest,
    service: Annotated[SignalService, Depends(get_signal_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> ExecuteLiveResponse:
    """Execute the signal against live asset properties from the connector."""
    return await service.execute_live(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        signal_id=signal_id,
        configurable_args=body.configurable_args,
        connector_instance_id=body.connector_instance_id,
    )

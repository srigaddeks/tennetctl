"""API routes for AI test-control linking."""
from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

from .dependencies import get_test_linker_service
from .schemas import (
    ApplyResult,
    ApplySuggestionsForControlRequest,
    ApplySuggestionsForTestRequest,
    BulkDecisionRequest,
    BulkDecisionResponse,
    BulkLinkJobResponse,
    BulkLinkRequest,
    JobStatusResponse,
    ListPendingMappingsQuery,
    PendingTestControlMappingListResponse,
    SuggestControlsRequest,
    SuggestTestsRequest,
)
from .service import TestLinkerService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/ai/test-linker", tags=["ai-test-linker"])


@router.post("/suggest-controls")
async def suggest_controls_for_test(
    payload: SuggestControlsRequest,
    service: Annotated[TestLinkerService, Depends(get_test_linker_service)],
    claims=Depends(get_current_access_claims),
):
    return await service.suggest_controls_for_test(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


@router.post("/suggest-tests")
async def suggest_tests_for_control(
    payload: SuggestTestsRequest,
    service: Annotated[TestLinkerService, Depends(get_test_linker_service)],
    claims=Depends(get_current_access_claims),
):
    return await service.suggest_tests_for_control(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


@router.post("/apply-for-test", response_model=ApplyResult)
async def apply_suggestions_for_test(
    payload: ApplySuggestionsForTestRequest,
    service: Annotated[TestLinkerService, Depends(get_test_linker_service)],
    claims=Depends(get_current_access_claims),
) -> ApplyResult:
    return await service.apply_suggestions(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


@router.post("/apply-for-control", response_model=ApplyResult)
async def apply_suggestions_for_control(
    payload: ApplySuggestionsForControlRequest,
    service: Annotated[TestLinkerService, Depends(get_test_linker_service)],
    claims=Depends(get_current_access_claims),
) -> ApplyResult:
    return await service.apply_suggestions_for_control(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


@router.post("/bulk-link", response_model=BulkLinkJobResponse, status_code=202)
async def bulk_link(
    payload: BulkLinkRequest,
    service: Annotated[TestLinkerService, Depends(get_test_linker_service)],
    claims=Depends(get_current_access_claims),
) -> BulkLinkJobResponse:
    return await service.enqueue_bulk_link(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    service: Annotated[TestLinkerService, Depends(get_test_linker_service)],
    claims=Depends(get_current_access_claims),
) -> JobStatusResponse:
    return await service.get_job_status(job_id=job_id, tenant_key=claims.tenant_key)


@router.post("/mappings/{mapping_id}/approve")
async def approve_mapping(
    mapping_id: str,
    service: Annotated[TestLinkerService, Depends(get_test_linker_service)],
    claims=Depends(get_current_access_claims),
):
    await service.approve_mapping(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        mapping_id=mapping_id,
    )
    return {"status": "approved"}


@router.post("/mappings/{mapping_id}/reject")
async def reject_mapping(
    mapping_id: str,
    service: Annotated[TestLinkerService, Depends(get_test_linker_service)],
    claims=Depends(get_current_access_claims),
):
    await service.reject_mapping(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        mapping_id=mapping_id,
    )
    return {"status": "rejected"}


@router.post("/mappings/bulk-approve", response_model=BulkDecisionResponse)
async def bulk_approve_mappings(
    payload: BulkDecisionRequest,
    service: Annotated[TestLinkerService, Depends(get_test_linker_service)],
    claims=Depends(get_current_access_claims),
) -> BulkDecisionResponse:
    return await service.bulk_approve_mappings(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


@router.post("/mappings/bulk-reject", response_model=BulkDecisionResponse)
async def bulk_reject_mappings(
    payload: BulkDecisionRequest,
    service: Annotated[TestLinkerService, Depends(get_test_linker_service)],
    claims=Depends(get_current_access_claims),
) -> BulkDecisionResponse:
    return await service.bulk_reject_mappings(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


@router.get("/pending", response_model=PendingTestControlMappingListResponse)
async def list_pending_mappings(
    service: Annotated[TestLinkerService, Depends(get_test_linker_service)],
    claims=Depends(get_current_access_claims),
    org_id: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
    framework_id: str | None = Query(default=None),
    control_ids: list[str] | None = Query(default=None),
    test_ids: list[str] | None = Query(default=None),
    created_after: str | None = Query(default=None),
    mine_only: bool = Query(default=False),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> PendingTestControlMappingListResponse:
    return await service.list_pending(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        query=ListPendingMappingsQuery(
            org_id=org_id,
            workspace_id=workspace_id,
            framework_id=framework_id,
            control_ids=control_ids,
            test_ids=test_ids,
            created_after=created_after,
            mine_only=mine_only,
            limit=limit,
            offset=offset,
        ),
    )

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_test_execution_service
from .schemas import (
    CreateTestExecutionRequest,
    UpdateTestExecutionRequest,
    TestExecutionResponse,
    TestExecutionListResponse,
)
from .service import TestExecutionService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/fr", tags=["grc-test-executions"])


@router.get("/test-executions", response_model=TestExecutionListResponse)
async def list_test_executions(
    service: Annotated[TestExecutionService, Depends(get_test_execution_service)],
    claims=Depends(get_current_access_claims),
    control_test_id: str | None = Query(None),
    control_id: str | None = Query(None),
    result_status: str | None = Query(None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> TestExecutionListResponse:
    return await service.list_executions(
        user_id=claims.subject,
        control_test_id=control_test_id,
        control_id=control_id,
        result_status=result_status,
        limit=limit,
        offset=offset,
    )


@router.get("/test-executions/{execution_id}", response_model=TestExecutionResponse)
async def get_test_execution(
    execution_id: str,
    service: Annotated[TestExecutionService, Depends(get_test_execution_service)],
    claims=Depends(get_current_access_claims),
) -> TestExecutionResponse:
    return await service.get_execution(user_id=claims.subject, execution_id=execution_id)


@router.post("/test-executions", response_model=TestExecutionResponse, status_code=status.HTTP_201_CREATED)
async def create_test_execution(
    body: CreateTestExecutionRequest,
    service: Annotated[TestExecutionService, Depends(get_test_execution_service)],
    claims=Depends(get_current_access_claims),
) -> TestExecutionResponse:
    return await service.create_execution(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body,
    )


@router.patch("/test-executions/{execution_id}", response_model=TestExecutionResponse)
async def update_test_execution(
    execution_id: str,
    body: UpdateTestExecutionRequest,
    service: Annotated[TestExecutionService, Depends(get_test_execution_service)],
    claims=Depends(get_current_access_claims),
) -> TestExecutionResponse:
    return await service.update_execution(
        user_id=claims.subject, execution_id=execution_id, request=body,
    )

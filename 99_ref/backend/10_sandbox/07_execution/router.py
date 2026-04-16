from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_execution_service
from .schemas import (
    BatchExecuteRequest,
    BatchExecuteResponse,
    ExecuteSignalRequest,
    PolicyExecutionListResponse,
    PolicyExecutionResponse,
    RunListResponse,
    RunResponse,
    ThreatEvaluationListResponse,
    ThreatEvaluationResponse,
)
from .service import ExecutionService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

# ── Runs ──────────────────────────────────────────────────────────

runs_router = InstrumentedAPIRouter(prefix="/api/v1/sb/runs", tags=["sandbox-execution"])


@runs_router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def execute_signal(
    body: ExecuteSignalRequest,
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> RunResponse:
    return await service.execute_signal(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        signal_id=body.signal_id,
        dataset_id=body.dataset_id,
    )


@runs_router.post("/batch", response_model=BatchExecuteResponse, status_code=status.HTTP_201_CREATED)
async def batch_execute(
    body: BatchExecuteRequest,
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> BatchExecuteResponse:
    return await service.batch_execute(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        signal_ids=body.signal_ids,
        dataset_id=body.dataset_id,
    )


@runs_router.get("", response_model=RunListResponse)
async def list_runs(
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    signal_id: str | None = Query(default=None),
    dataset_id: str | None = Query(default=None),
    execution_status_code: str | None = Query(default=None),
    result_code: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> RunListResponse:
    return await service.list_runs(
        user_id=claims.subject,
        org_id=org_id,
        signal_id=signal_id,
        dataset_id=dataset_id,
        execution_status_code=execution_status_code,
        result_code=result_code,
        limit=limit,
        offset=offset,
    )


@runs_router.get("/history")
async def query_history(
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    signal_code: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=500, ge=1, le=10000),
) -> list[dict]:
    return await service.query_history(
        user_id=claims.subject,
        org_id=org_id,
        signal_code=signal_code,
        days=days,
        limit=limit,
    )


@runs_router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: str,
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    claims=Depends(get_current_access_claims),
) -> RunResponse:
    return await service.get_run(
        user_id=claims.subject,
        run_id=run_id,
    )


# ── Threat Evaluations ───────────────────────────────────────────

threat_eval_router = InstrumentedAPIRouter(prefix="/api/v1/sb/threat-evaluations", tags=["sandbox-execution"])


@threat_eval_router.get("", response_model=ThreatEvaluationListResponse)
async def list_threat_evaluations(
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    threat_type_id: str | None = Query(default=None),
    is_triggered: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> ThreatEvaluationListResponse:
    return await service.list_threat_evaluations(
        user_id=claims.subject,
        org_id=org_id,
        threat_type_id=threat_type_id,
        is_triggered=is_triggered,
        limit=limit,
        offset=offset,
    )


@threat_eval_router.get("/{eval_id}", response_model=ThreatEvaluationResponse)
async def get_threat_evaluation(
    eval_id: str,
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    claims=Depends(get_current_access_claims),
) -> ThreatEvaluationResponse:
    return await service.get_threat_evaluation(
        user_id=claims.subject,
        eval_id=eval_id,
    )


# ── Policy Executions ────────────────────────────────────────────

policy_exec_router = InstrumentedAPIRouter(prefix="/api/v1/sb/policy-executions", tags=["sandbox-execution"])


@policy_exec_router.get("", response_model=PolicyExecutionListResponse)
async def list_policy_executions(
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    policy_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> PolicyExecutionListResponse:
    return await service.list_policy_executions(
        user_id=claims.subject,
        org_id=org_id,
        policy_id=policy_id,
        limit=limit,
        offset=offset,
    )


@policy_exec_router.get("/{exec_id}", response_model=PolicyExecutionResponse)
async def get_policy_execution(
    exec_id: str,
    service: Annotated[ExecutionService, Depends(get_execution_service)],
    claims=Depends(get_current_access_claims),
) -> PolicyExecutionResponse:
    return await service.get_policy_execution(
        user_id=claims.subject,
        exec_id=exec_id,
    )

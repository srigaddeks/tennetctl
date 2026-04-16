from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

from .dependencies import get_agent_execution_service
from .schemas import (
    AgentRunListResponse,
    AgentRunResponse,
    AgentRunStepResponse,
    CompileCheckRequest,
    CompileCheckResponse,
    ExecuteAgentRequest,
)
from .service import AgentExecutionService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/asb", tags=["agent-sandbox-execution"])


# ── compile check ─────────────────────────────────────────

@router.post("/compile-check", response_model=CompileCheckResponse)
async def compile_check(
    request: CompileCheckRequest,
    service: Annotated[AgentExecutionService, Depends(get_agent_execution_service)],
    claims=Depends(get_current_access_claims),
) -> CompileCheckResponse:
    return await service.compile_check(graph_source=request.graph_source)


# ── execute ───────────────────────────────────────────────

@router.post("/agents/{agent_id}/execute", response_model=AgentRunResponse, status_code=201)
async def execute_agent(
    agent_id: str,
    request: ExecuteAgentRequest,
    service: Annotated[AgentExecutionService, Depends(get_agent_execution_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> AgentRunResponse:
    return await service.execute_agent(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        agent_id=agent_id,
        input_messages=request.input_messages,
        initial_context=request.initial_context,
    )


# ── runs ──────────────────────────────────────────────────

@router.get("/runs", response_model=AgentRunListResponse)
async def list_runs(
    service: Annotated[AgentExecutionService, Depends(get_agent_execution_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
    agent_id: str | None = Query(None, description="Filter by agent"),
    execution_status_code: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> AgentRunListResponse:
    return await service.list_runs(
        user_id=claims.subject,
        org_id=org_id,
        agent_id=agent_id,
        execution_status_code=execution_status_code,
        limit=limit,
        offset=offset,
    )


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_run(
    run_id: str,
    service: Annotated[AgentExecutionService, Depends(get_agent_execution_service)],
    claims=Depends(get_current_access_claims),
) -> AgentRunResponse:
    return await service.get_run(user_id=claims.subject, run_id=run_id)


@router.get("/runs/{run_id}/steps", response_model=list[AgentRunStepResponse])
async def get_run_steps(
    run_id: str,
    service: Annotated[AgentExecutionService, Depends(get_agent_execution_service)],
    claims=Depends(get_current_access_claims),
) -> list[AgentRunStepResponse]:
    return await service.get_run_steps(user_id=claims.subject, run_id=run_id)


@router.post("/runs/{run_id}/cancel", response_model=AgentRunResponse)
async def cancel_run(
    run_id: str,
    service: Annotated[AgentExecutionService, Depends(get_agent_execution_service)],
    claims=Depends(get_current_access_claims),
) -> AgentRunResponse:
    return await service.cancel_run(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        run_id=run_id,
    )

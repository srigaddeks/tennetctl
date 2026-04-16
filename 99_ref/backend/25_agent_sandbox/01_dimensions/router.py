from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

from .dependencies import get_agent_sandbox_dimension_service
from .service import AgentSandboxDimensionService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/asb/dimensions", tags=["agent-sandbox-dimensions"])


@router.get("/stats")
async def get_agent_sandbox_stats(
    service: Annotated[AgentSandboxDimensionService, Depends(get_agent_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
):
    return await service.get_stats(user_id=claims.subject, org_id=org_id)


@router.get("/agent-statuses")
async def list_agent_statuses(
    service: Annotated[AgentSandboxDimensionService, Depends(get_agent_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[dict]:
    return await service.list_dimension(dimension_name="agent_statuses")


@router.get("/tool-types")
async def list_tool_types(
    service: Annotated[AgentSandboxDimensionService, Depends(get_agent_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[dict]:
    return await service.list_dimension(dimension_name="tool_types")


@router.get("/scenario-types")
async def list_scenario_types(
    service: Annotated[AgentSandboxDimensionService, Depends(get_agent_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[dict]:
    return await service.list_dimension(dimension_name="scenario_types")


@router.get("/evaluation-methods")
async def list_evaluation_methods(
    service: Annotated[AgentSandboxDimensionService, Depends(get_agent_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[dict]:
    return await service.list_dimension(dimension_name="evaluation_methods")


@router.get("/execution-statuses")
async def list_execution_statuses(
    service: Annotated[AgentSandboxDimensionService, Depends(get_agent_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[dict]:
    return await service.list_dimension(dimension_name="execution_statuses")

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

from .dependencies import get_test_scenario_service
from .schemas import (
    AddTestCaseRequest,
    CreateScenarioRequest,
    ScenarioListResponse,
    ScenarioResponse,
    TestCaseResponse,
)
from .service import TestScenarioService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/asb/scenarios", tags=["agent-sandbox-scenarios"])


@router.get("/", response_model=ScenarioListResponse)
async def list_scenarios(
    service: Annotated[TestScenarioService, Depends(get_test_scenario_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
    agent_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ScenarioListResponse:
    return await service.list_scenarios(
        user_id=claims.subject, org_id=org_id,
        agent_id=agent_id, limit=limit, offset=offset,
    )


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    service: Annotated[TestScenarioService, Depends(get_test_scenario_service)],
    claims=Depends(get_current_access_claims),
) -> ScenarioResponse:
    return await service.get_scenario(user_id=claims.subject, scenario_id=scenario_id)


@router.post("/", response_model=ScenarioResponse, status_code=201)
async def create_scenario(
    request: CreateScenarioRequest,
    service: Annotated[TestScenarioService, Depends(get_test_scenario_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> ScenarioResponse:
    return await service.create_scenario(
        user_id=claims.subject, tenant_key=claims.tenant_key,
        org_id=org_id, request=request,
    )


@router.delete("/{scenario_id}", status_code=204)
async def delete_scenario(
    scenario_id: str,
    service: Annotated[TestScenarioService, Depends(get_test_scenario_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> None:
    await service.delete_scenario(
        user_id=claims.subject, tenant_key=claims.tenant_key,
        org_id=org_id, scenario_id=scenario_id,
    )


@router.post("/{scenario_id}/cases", response_model=TestCaseResponse, status_code=201)
async def add_test_case(
    scenario_id: str,
    request: AddTestCaseRequest,
    service: Annotated[TestScenarioService, Depends(get_test_scenario_service)],
    claims=Depends(get_current_access_claims),
) -> TestCaseResponse:
    return await service.add_test_case(
        user_id=claims.subject, scenario_id=scenario_id, request=request,
    )

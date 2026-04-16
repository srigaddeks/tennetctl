from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

from .dependencies import get_test_runner_service
from .service import TestRunnerService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/asb", tags=["agent-sandbox-test-runner"])


@router.post("/scenarios/{scenario_id}/run")
async def run_scenario(
    scenario_id: str,
    service: Annotated[TestRunnerService, Depends(get_test_runner_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
    agent_id: str | None = Query(None, description="Override agent to test"),
) -> dict:
    return await service.run_scenario(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        scenario_id=scenario_id,
        agent_id=agent_id,
    )


@router.get("/test-results")
async def list_test_results(
    service: Annotated[TestRunnerService, Depends(get_test_runner_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    return await service.list_test_results(
        user_id=claims.subject, org_id=org_id, limit=limit, offset=offset,
    )

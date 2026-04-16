from __future__ import annotations
from importlib import import_module
from typing import Annotated
from fastapi import Depends

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_service_module = import_module("backend.20_ai.07_reporting.service")
_schemas_module = import_module("backend.20_ai.07_reporting.schemas")
_deps_module = import_module("backend.20_ai.07_reporting.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims
ReportingService = _service_module.ReportingService
AISummaryResponse = _schemas_module.AISummaryResponse
AgentRunStats = _schemas_module.AgentRunStats
get_reporting_service = _deps_module.get_reporting_service

router = InstrumentedAPIRouter(prefix="/api/v1/ai/reporting", tags=["ai-reporting"])

@router.get("/summary", response_model=AISummaryResponse)
async def get_summary(service: Annotated[ReportingService, Depends(get_reporting_service)],
        claims: Annotated[dict, Depends(get_current_access_claims)]) -> AISummaryResponse:
    return await service.get_summary(caller_id=claims.subject, tenant_key=claims.tenant_key)

@router.get("/agent-runs", response_model=list[AgentRunStats])
async def get_agent_run_stats(service: Annotated[ReportingService, Depends(get_reporting_service)],
        claims: Annotated[dict, Depends(get_current_access_claims)]) -> list[AgentRunStats]:
    return await service.get_agent_run_stats(caller_id=claims.subject, tenant_key=claims.tenant_key)

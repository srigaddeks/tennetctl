from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

from .dependencies import get_agent_service
from .schemas import (
    AgentListResponse,
    AgentResponse,
    AgentVersionResponse,
    BindToolRequest,
    CreateAgentRequest,
    UpdateAgentRequest,
)
from .service import AgentService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/asb/agents", tags=["agent-sandbox-agents"])


@router.get("/", response_model=AgentListResponse)
async def list_agents(
    service: Annotated[AgentService, Depends(get_agent_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
    workspace_id: str | None = Query(None, description="Filter by workspace"),
    agent_status_code: str | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search by name or code"),
    sort_by: str = Query("created_at", description="Sort column"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> AgentListResponse:
    return await service.list_agents(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        agent_status_code=agent_status_code,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    service: Annotated[AgentService, Depends(get_agent_service)],
    claims=Depends(get_current_access_claims),
) -> AgentResponse:
    return await service.get_agent(user_id=claims.subject, agent_id=agent_id)


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent(
    request: CreateAgentRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> AgentResponse:
    if not request.workspace_id:
        pass  # org-scoped by default
    return await service.create_agent(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=request,
    )


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> AgentResponse:
    return await service.update_agent(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        agent_id=agent_id,
        request=request,
    )


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    service: Annotated[AgentService, Depends(get_agent_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> None:
    await service.delete_agent(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        agent_id=agent_id,
    )


@router.get("/{agent_code}/versions", response_model=list[AgentVersionResponse])
async def list_agent_versions(
    agent_code: str,
    service: Annotated[AgentService, Depends(get_agent_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> list[AgentVersionResponse]:
    return await service.list_versions(
        user_id=claims.subject,
        org_id=org_id,
        agent_code=agent_code,
    )


# ── tool bindings ─────────────────────────────────────────

@router.get("/{agent_id}/tools")
async def list_bound_tools(
    agent_id: str,
    service: Annotated[AgentService, Depends(get_agent_service)],
    claims=Depends(get_current_access_claims),
) -> list[dict]:
    return await service.list_bound_tools(user_id=claims.subject, agent_id=agent_id)


@router.post("/{agent_id}/tools", status_code=201)
async def bind_tool(
    agent_id: str,
    request: BindToolRequest,
    service: Annotated[AgentService, Depends(get_agent_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> dict:
    await service.bind_tool(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        agent_id=agent_id,
        tool_id=request.tool_id,
        sort_order=request.sort_order,
    )
    return {"status": "bound"}


@router.delete("/{agent_id}/tools/{tool_id}", status_code=204)
async def unbind_tool(
    agent_id: str,
    tool_id: str,
    service: Annotated[AgentService, Depends(get_agent_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> None:
    await service.unbind_tool(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        agent_id=agent_id,
        tool_id=tool_id,
    )

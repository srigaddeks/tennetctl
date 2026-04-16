from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

from .dependencies import get_agent_tool_service
from .schemas import (
    CreateToolRequest,
    ToolListResponse,
    ToolResponse,
    UpdateToolRequest,
)
from .service import AgentToolService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/asb/tools", tags=["agent-sandbox-tools"])


@router.get("/", response_model=ToolListResponse)
async def list_tools(
    service: Annotated[AgentToolService, Depends(get_agent_tool_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
    tool_type_code: str | None = Query(None, description="Filter by tool type"),
    search: str | None = Query(None, description="Search by name or code"),
    sort_by: str = Query("created_at", description="Sort column"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ToolListResponse:
    return await service.list_tools(
        user_id=claims.subject,
        org_id=org_id,
        tool_type_code=tool_type_code,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: str,
    service: Annotated[AgentToolService, Depends(get_agent_tool_service)],
    claims=Depends(get_current_access_claims),
) -> ToolResponse:
    return await service.get_tool(user_id=claims.subject, tool_id=tool_id)


@router.post("/", response_model=ToolResponse, status_code=201)
async def create_tool(
    request: CreateToolRequest,
    service: Annotated[AgentToolService, Depends(get_agent_tool_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> ToolResponse:
    return await service.create_tool(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=request,
    )


@router.patch("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: str,
    request: UpdateToolRequest,
    service: Annotated[AgentToolService, Depends(get_agent_tool_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> ToolResponse:
    return await service.update_tool(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        tool_id=tool_id,
        request=request,
    )


@router.delete("/{tool_id}", status_code=204)
async def delete_tool(
    tool_id: str,
    service: Annotated[AgentToolService, Depends(get_agent_tool_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
) -> None:
    await service.delete_tool(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        tool_id=tool_id,
    )

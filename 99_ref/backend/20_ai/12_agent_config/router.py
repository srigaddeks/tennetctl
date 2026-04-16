from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_service_module = import_module("backend.20_ai.12_agent_config.service")
_schemas_module = import_module("backend.20_ai.12_agent_config.schemas")
_deps_module = import_module("backend.20_ai.12_agent_config.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims
AgentConfigService = _service_module.AgentConfigService
AgentConfigListResponse = _schemas_module.AgentConfigListResponse
AgentConfigResponse = _schemas_module.AgentConfigResponse
CreateAgentConfigRequest = _schemas_module.CreateAgentConfigRequest
UpdateAgentConfigRequest = _schemas_module.UpdateAgentConfigRequest
get_agent_config_service = _deps_module.get_agent_config_service

router = InstrumentedAPIRouter(prefix="/api/v1/ai/admin/agent-configs", tags=["ai-admin"])


@router.get("", response_model=AgentConfigListResponse)
async def list_agent_configs(
    service: Annotated[AgentConfigService, Depends(get_agent_config_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    agent_type_code: str | None = Query(None),
    org_id: str | None = Query(None),
) -> AgentConfigListResponse:
    return await service.list_configs(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        agent_type_code=agent_type_code,
        org_id=org_id,
    )


@router.get("/{config_id}", response_model=AgentConfigResponse)
async def get_agent_config(
    config_id: str,
    service: Annotated[AgentConfigService, Depends(get_agent_config_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> AgentConfigResponse:
    return await service.get_config(
        config_id=config_id,
        tenant_key=claims.tenant_key,
        user_id=claims.subject,
    )


@router.post("", response_model=AgentConfigResponse, status_code=201)
async def create_agent_config(
    request: CreateAgentConfigRequest,
    service: Annotated[AgentConfigService, Depends(get_agent_config_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> AgentConfigResponse:
    return await service.create_config(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=request,
    )


@router.patch("/{config_id}", response_model=AgentConfigResponse)
async def update_agent_config(
    config_id: str,
    request: UpdateAgentConfigRequest,
    service: Annotated[AgentConfigService, Depends(get_agent_config_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> AgentConfigResponse:
    return await service.update_config(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        config_id=config_id,
        request=request,
    )


@router.delete("/{config_id}", status_code=204)
async def delete_agent_config(
    config_id: str,
    service: Annotated[AgentConfigService, Depends(get_agent_config_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> None:
    await service.delete_config(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        config_id=config_id,
    )

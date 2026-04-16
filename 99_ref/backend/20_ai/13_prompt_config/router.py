from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_service_module = import_module("backend.20_ai.13_prompt_config.service")
_schemas_module = import_module("backend.20_ai.13_prompt_config.schemas")
_deps_module = import_module("backend.20_ai.13_prompt_config.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims
PromptConfigService = _service_module.PromptConfigService
PromptTemplateListResponse = _schemas_module.PromptTemplateListResponse
PromptTemplateResponse = _schemas_module.PromptTemplateResponse
CreatePromptTemplateRequest = _schemas_module.CreatePromptTemplateRequest
UpdatePromptTemplateRequest = _schemas_module.UpdatePromptTemplateRequest
PromptPreviewRequest = _schemas_module.PromptPreviewRequest
PromptPreviewResponse = _schemas_module.PromptPreviewResponse
get_prompt_config_service = _deps_module.get_prompt_config_service

router = InstrumentedAPIRouter(prefix="/api/v1/ai/admin/prompts", tags=["ai-admin"])


@router.get("", response_model=PromptTemplateListResponse)
async def list_prompt_templates(
    service: Annotated[PromptConfigService, Depends(get_prompt_config_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    scope_code: str | None = Query(None),
    agent_type_code: str | None = Query(None),
    feature_code: str | None = Query(None),
    org_id: str | None = Query(None),
) -> PromptTemplateListResponse:
    return await service.list_templates(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        scope_code=scope_code,
        agent_type_code=agent_type_code,
        feature_code=feature_code,
        org_id=org_id,
    )


@router.post("/preview", response_model=PromptPreviewResponse)
async def preview_prompt(
    request: PromptPreviewRequest,
    service: Annotated[PromptConfigService, Depends(get_prompt_config_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> PromptPreviewResponse:
    return await service.preview_prompt(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=request,
    )


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: str,
    service: Annotated[PromptConfigService, Depends(get_prompt_config_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> PromptTemplateResponse:
    return await service.get_template(
        template_id=template_id,
        tenant_key=claims.tenant_key,
        user_id=claims.subject,
    )


@router.post("", response_model=PromptTemplateResponse, status_code=201)
async def create_prompt_template(
    request: CreatePromptTemplateRequest,
    service: Annotated[PromptConfigService, Depends(get_prompt_config_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> PromptTemplateResponse:
    return await service.create_template(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=request,
    )


@router.patch("/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: str,
    request: UpdatePromptTemplateRequest,
    service: Annotated[PromptConfigService, Depends(get_prompt_config_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> PromptTemplateResponse:
    return await service.update_template(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        template_id=template_id,
        request=request,
    )


@router.delete("/{template_id}", status_code=204)
async def delete_prompt_template(
    template_id: str,
    service: Annotated[PromptConfigService, Depends(get_prompt_config_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> None:
    await service.delete_template(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        template_id=template_id,
    )

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_template_service
from .schemas import (
    CreateTemplateRequest,
    CreateTemplateVersionRequest,
    PreviewTemplateRequest,
    PreviewTemplateResponse,
    RenderRawRequest,
    TemplateDetailResponse,
    TemplateListResponse,
    TemplateResponse,
    TemplateVersionResponse,
    UpdateTemplateRequest,
)
from .service import TemplateService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/notifications", tags=["notification-templates"])


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    service: Annotated[TemplateService, Depends(get_template_service)],
    claims=Depends(get_current_access_claims),
    include_test: bool = Query(False, description="Include test/debug templates (default: false)"),
) -> TemplateListResponse:
    return await service.list_templates(
        user_id=claims.subject, tenant_key=claims.tenant_key, include_test=include_test
    )


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: str,
    service: Annotated[TemplateService, Depends(get_template_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_template(
        user_id=claims.subject, template_id=template_id, tenant_key=claims.tenant_key
    )


@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    body: CreateTemplateRequest,
    service: Annotated[TemplateService, Depends(get_template_service)],
    claims=Depends(get_current_access_claims),
) -> TemplateResponse:
    return await service.create_template(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


@router.post("/templates/render-raw", response_model=PreviewTemplateResponse)
async def render_raw(
    body: RenderRawRequest,
    service: Annotated[TemplateService, Depends(get_template_service)],
    claims=Depends(get_current_access_claims),
) -> PreviewTemplateResponse:
    return await service.render_raw(user_id=claims.subject, request=body)


@router.get("/templates/{template_id}", response_model=TemplateDetailResponse)
async def get_template(
    template_id: str,
    service: Annotated[TemplateService, Depends(get_template_service)],
    claims=Depends(get_current_access_claims),
) -> TemplateDetailResponse:
    return await service.get_template_detail(user_id=claims.subject, template_id=template_id)


@router.patch("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: str,
    body: UpdateTemplateRequest,
    service: Annotated[TemplateService, Depends(get_template_service)],
    claims=Depends(get_current_access_claims),
) -> TemplateResponse:
    return await service.update_template(user_id=claims.subject, template_id=template_id, request=body)


@router.post(
    "/templates/{template_id}/versions",
    response_model=TemplateVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_version(
    template_id: str,
    body: CreateTemplateVersionRequest,
    service: Annotated[TemplateService, Depends(get_template_service)],
    claims=Depends(get_current_access_claims),
) -> TemplateVersionResponse:
    return await service.create_version(user_id=claims.subject, template_id=template_id, request=body)


@router.post("/templates/{template_id}/preview", response_model=PreviewTemplateResponse)
async def preview_template(
    template_id: str,
    body: PreviewTemplateRequest,
    service: Annotated[TemplateService, Depends(get_template_service)],
    claims=Depends(get_current_access_claims),
) -> PreviewTemplateResponse:
    return await service.preview_template(
        user_id=claims.subject, template_id=template_id, variables=body.variables
    )

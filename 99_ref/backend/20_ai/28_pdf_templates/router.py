"""
FastAPI routes for PDF Report Templates.
Prefix: /api/v1/ai/pdf-templates
"""
from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, File, Query, UploadFile, status

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_svc_module = import_module("backend.20_ai.28_pdf_templates.service")
_schemas_module = import_module("backend.20_ai.28_pdf_templates.schemas")
_deps_module = import_module("backend.20_ai.28_pdf_templates.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims
PdfTemplateService = _svc_module.PdfTemplateService
CreatePdfTemplateRequest = _schemas_module.CreatePdfTemplateRequest
UpdatePdfTemplateRequest = _schemas_module.UpdatePdfTemplateRequest
PdfTemplateResponse = _schemas_module.PdfTemplateResponse
PdfTemplateListResponse = _schemas_module.PdfTemplateListResponse
get_pdf_template_service = _deps_module.get_pdf_template_service

router = InstrumentedAPIRouter(
    prefix="/api/v1/ai/pdf-templates",
    tags=["ai-pdf-templates"],
)


@router.post("", response_model=PdfTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_pdf_template(
    body: CreatePdfTemplateRequest,
    service: Annotated[PdfTemplateService, Depends(get_pdf_template_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> PdfTemplateResponse:
    """Create a new PDF report template."""
    return await service.create_template(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=body,
    )


@router.get("", response_model=PdfTemplateListResponse)
async def list_pdf_templates(
    service: Annotated[PdfTemplateService, Depends(get_pdf_template_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    report_type: str | None = Query(None),
    is_default: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> PdfTemplateListResponse:
    """List PDF templates, optionally filtered by report_type and/or is_default."""
    return await service.list_templates(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        report_type=report_type,
        is_default=is_default,
        limit=limit,
        offset=offset,
    )


@router.get("/{template_id}", response_model=PdfTemplateResponse)
async def get_pdf_template(
    template_id: str,
    service: Annotated[PdfTemplateService, Depends(get_pdf_template_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> PdfTemplateResponse:
    """Get a PDF template by ID."""
    return await service.get_template(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        template_id=template_id,
    )


@router.patch("/{template_id}", response_model=PdfTemplateResponse)
async def update_pdf_template(
    template_id: str,
    body: UpdatePdfTemplateRequest,
    service: Annotated[PdfTemplateService, Depends(get_pdf_template_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> PdfTemplateResponse:
    """Update a PDF template."""
    return await service.update_template(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        template_id=template_id,
        request=body,
    )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pdf_template(
    template_id: str,
    service: Annotated[PdfTemplateService, Depends(get_pdf_template_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> None:
    """Delete a PDF template."""
    await service.delete_template(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        template_id=template_id,
    )


@router.post("/{template_id}/set-default", response_model=PdfTemplateResponse)
async def set_pdf_template_default(
    template_id: str,
    service: Annotated[PdfTemplateService, Depends(get_pdf_template_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> PdfTemplateResponse:
    """Set a template as the default for its applicable report types."""
    return await service.set_default(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        template_id=template_id,
    )


@router.post(
    "/{template_id}/upload-shell",
    response_model=PdfTemplateResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_shell_pdf(
    template_id: str,
    service: Annotated[PdfTemplateService, Depends(get_pdf_template_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    file: UploadFile = File(...),
) -> PdfTemplateResponse:
    """Upload a PDF shell file to use as the template base."""
    file_data = await file.read()
    return await service.upload_shell_pdf(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        template_id=template_id,
        file_data=file_data,
        filename=file.filename or "shell.pdf",
    )

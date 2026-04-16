from __future__ import annotations
from importlib import import_module
from typing import Annotated
from fastapi import Depends, File, Query, UploadFile

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_svc_module = import_module("backend.20_ai.19_attachments.service")
_schemas_module = import_module("backend.20_ai.19_attachments.schemas")
_deps_module = import_module("backend.20_ai.19_attachments.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims
AttachmentService = _svc_module.AttachmentService
AttachmentResponse = _schemas_module.AttachmentResponse
AttachmentListResponse = _schemas_module.AttachmentListResponse
get_attachment_service = _deps_module.get_attachment_service

router = InstrumentedAPIRouter(
    prefix="/api/v1/ai/conversations",
    tags=["ai-attachments"],
)


@router.post(
    "/{conversation_id}/attachments",
    response_model=AttachmentResponse,
    status_code=201,
)
async def upload_attachment(
    conversation_id: str,
    file: Annotated[UploadFile, File(description="Document to attach (PDF, DOCX, TXT, CSV, JSON, MD, HTML)")],
    service: Annotated[AttachmentService, Depends(get_attachment_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    org_id: str = Query(...),
    workspace_id: str = Query(...),
) -> AttachmentResponse:
    """
    Upload a document to a conversation. The file is chunked, embedded, and
    stored in the kcontrol_copilot Qdrant collection so the AI can reference it.
    """
    file_bytes = await file.read()
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "attachment"
    return await service.upload_and_ingest(
        conversation_id=conversation_id,
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        filename=filename,
        content_type=content_type,
        file_bytes=file_bytes,
    )


@router.get(
    "/{conversation_id}/attachments",
    response_model=AttachmentListResponse,
)
async def list_attachments(
    conversation_id: str,
    service: Annotated[AttachmentService, Depends(get_attachment_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    org_id: str = Query(...),
    workspace_id: str = Query(...),
) -> AttachmentListResponse:
    return await service.list_attachments(
        conversation_id=conversation_id,
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
    )


@router.delete("/{conversation_id}/attachments/{attachment_id}", status_code=204)
async def delete_attachment(
    conversation_id: str,
    attachment_id: str,
    service: Annotated[AttachmentService, Depends(get_attachment_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    org_id: str = Query(...),
    workspace_id: str = Query(...),
) -> None:
    await service.delete_attachment(
        conversation_id=conversation_id,
        attachment_id=attachment_id,
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
    )

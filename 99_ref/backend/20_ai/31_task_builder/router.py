"""
API routes for AI task builder — session-based async flow + legacy direct endpoints.

Prefix: /api/v1/ai/task-builder

Session-based (new):
  POST   /sessions                          Create a new task builder session
  GET    /sessions                          List user's sessions (history)
  GET    /sessions/{id}                     Get session detail
  PATCH  /sessions/{id}                     Update context/attachments
  POST   /sessions/{id}/enqueue-preview     Enqueue preview job (async, survives navigation)
  POST   /sessions/{id}/enqueue-apply       Enqueue apply job (async, survives navigation)
  GET    /sessions/{id}/job                 Poll session's job status
  GET    /jobs/{job_id}                     Poll any task builder job by ID

Legacy (kept for backwards compat):
  POST   /upload                            Upload attachment
  POST   /preview                           Synchronous preview
  POST   /apply                             Synchronous apply
"""

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, File, Query, UploadFile


_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_schemas_module = import_module("backend.20_ai.31_task_builder.schemas")
_deps_module = import_module("backend.20_ai.31_task_builder.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims
PreviewRequest = _schemas_module.PreviewRequest
ApplyRequest = _schemas_module.ApplyRequest
ApplyResponse = _schemas_module.ApplyResponse
TaskGroupResponse = _schemas_module.TaskGroupResponse
CreateTaskBuilderSessionRequest = _schemas_module.CreateTaskBuilderSessionRequest
PatchTaskBuilderSessionRequest = _schemas_module.PatchTaskBuilderSessionRequest
TaskBuilderSessionResponse = _schemas_module.TaskBuilderSessionResponse
TaskBuilderSessionListResponse = _schemas_module.TaskBuilderSessionListResponse
TaskBuilderJobStatusResponse = _schemas_module.TaskBuilderJobStatusResponse
TaskBuilderService = _deps_module.TaskBuilderService
get_task_builder_service = _deps_module.get_task_builder_service

router = InstrumentedAPIRouter(prefix="/api/v1/ai/task-builder", tags=["ai-task-builder"])


# ── Session CRUD ─────────────────────────────────────────────────────────────


@router.post("/sessions", response_model=TaskBuilderSessionResponse, status_code=201)
async def create_session(
    payload: CreateTaskBuilderSessionRequest,
    service: Annotated[TaskBuilderService, Depends(get_task_builder_service)],
    claims=Depends(get_current_access_claims),
) -> TaskBuilderSessionResponse:
    """Create a new task builder session."""
    return await service.create_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


@router.get("/sessions", response_model=TaskBuilderSessionListResponse)
async def list_sessions(
    service: Annotated[TaskBuilderService, Depends(get_task_builder_service)],
    claims=Depends(get_current_access_claims),
    framework_id: str | None = Query(default=None),
    scope_org_id: str | None = Query(default=None),
    scope_workspace_id: str | None = Query(default=None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> TaskBuilderSessionListResponse:
    """List task builder sessions for the current user."""
    return await service.list_sessions(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        scope_org_id=scope_org_id,
        scope_workspace_id=scope_workspace_id,
        limit=limit,
        offset=offset,
    )


@router.get("/sessions/{session_id}", response_model=TaskBuilderSessionResponse)
async def get_session(
    session_id: str,
    service: Annotated[TaskBuilderService, Depends(get_task_builder_service)],
    claims=Depends(get_current_access_claims),
) -> TaskBuilderSessionResponse:
    return await service.get_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
    )


@router.patch("/sessions/{session_id}", response_model=TaskBuilderSessionResponse)
async def patch_session(
    session_id: str,
    payload: PatchTaskBuilderSessionRequest,
    service: Annotated[TaskBuilderService, Depends(get_task_builder_service)],
    claims=Depends(get_current_access_claims),
) -> TaskBuilderSessionResponse:
    """Update context, attachments, or control selection on an existing session."""
    return await service.patch_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
        request=payload,
    )


# ── Enqueue Preview (async, survives navigation) ─────────────────────────────


@router.post("/sessions/{session_id}/enqueue-preview", response_model=TaskBuilderJobStatusResponse, status_code=202)
async def enqueue_preview(
    session_id: str,
    service: Annotated[TaskBuilderService, Depends(get_task_builder_service)],
    claims=Depends(get_current_access_claims),
) -> TaskBuilderJobStatusResponse:
    """Enqueue task preview generation as a background job. User can navigate away."""
    return await service.enqueue_preview(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
    )


# ── Enqueue Apply (async, survives navigation) ───────────────────────────────


class EnqueueApplyBody(_schemas_module.BaseModel):
    task_groups: list[dict] | None = None


@router.post("/sessions/{session_id}/enqueue-apply", response_model=TaskBuilderJobStatusResponse, status_code=202)
async def enqueue_apply(
    session_id: str,
    service: Annotated[TaskBuilderService, Depends(get_task_builder_service)],
    claims=Depends(get_current_access_claims),
    body: EnqueueApplyBody | None = None,
) -> TaskBuilderJobStatusResponse:
    """Enqueue task creation as a background job. Optionally pass filtered task_groups."""
    return await service.enqueue_apply(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
        task_groups=body.task_groups if body else None,
    )


# ── Poll Job Status ──────────────────────────────────────────────────────────


@router.get("/sessions/{session_id}/job", response_model=TaskBuilderJobStatusResponse)
async def get_session_job(
    session_id: str,
    service: Annotated[TaskBuilderService, Depends(get_task_builder_service)],
    claims=Depends(get_current_access_claims),
) -> TaskBuilderJobStatusResponse:
    """Poll the job status for a session."""
    session = await service.get_session(
        session_id=session_id, user_id=claims.subject, tenant_key=claims.tenant_key
    )
    if not session.job_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No background job found for this session")

    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Polling job status for session {session_id}, job {session.job_id}")

    return await service.get_job_status(
        user_id=claims.subject, tenant_key=claims.tenant_key, job_id=session.job_id,
    )


@router.get("/jobs/{job_id}", response_model=TaskBuilderJobStatusResponse)
async def get_job(
    job_id: str,
    service: Annotated[TaskBuilderService, Depends(get_task_builder_service)],
    claims=Depends(get_current_access_claims),
) -> TaskBuilderJobStatusResponse:
    """Poll any task builder job by ID."""
    return await service.get_job_status(
        user_id=claims.subject, tenant_key=claims.tenant_key, job_id=job_id,
    )


# ── Legacy endpoints (kept for backwards compat) ─────────────────────────────


@router.post("/upload", status_code=201)
async def upload_attachment(
    file: Annotated[UploadFile, File(description="Document to attach (PDF, DOCX, TXT, CSV, JSON, MD)")],
    service: Annotated[TaskBuilderService, Depends(get_task_builder_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str = Query(...),
) -> dict:
    """Upload a document to provide context for task generation."""
    file_bytes = await file.read()
    return await service.upload_attachment(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        filename=file.filename or "attachment",
        content_type=file.content_type or "application/octet-stream",
        file_bytes=file_bytes,
    )


@router.post("/preview", response_model=list[TaskGroupResponse])
async def preview_tasks(
    body: PreviewRequest,
    service: Annotated[TaskBuilderService, Depends(get_task_builder_service)],
    claims=Depends(get_current_access_claims),
) -> list[TaskGroupResponse]:
    """Generate task suggestions without writing anything to the database."""
    return await service.preview_tasks(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        framework_id=body.framework_id,
        org_id=body.org_id,
        workspace_id=body.workspace_id,
        user_context=body.user_context,
        control_ids=body.control_ids,
        attachment_ids=body.attachment_ids,
    )


@router.post("/apply", response_model=ApplyResponse)
async def apply_tasks(
    body: ApplyRequest,
    service: Annotated[TaskBuilderService, Depends(get_task_builder_service)],
    claims=Depends(get_current_access_claims),
) -> ApplyResponse:
    """Create reviewed tasks in the database while skipping duplicates."""
    return await service.apply_tasks(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=body.org_id,
        workspace_id=body.workspace_id,
        framework_id=body.framework_id,
        task_groups=body.task_groups,
    )

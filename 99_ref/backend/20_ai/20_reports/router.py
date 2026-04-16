"""
FastAPI routes for the GRC Report Generation module.
Prefix: /api/v1/ai/reports
"""

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request, File, Form, UploadFile
from fastapi.responses import Response, StreamingResponse

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_svc_module = import_module("backend.20_ai.20_reports.service")
_schemas_module = import_module("backend.20_ai.20_reports.schemas")
_deps_module = import_module("backend.20_ai.20_reports.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims
ReportService = _svc_module.ReportService
GenerateReportRequest = _schemas_module.GenerateReportRequest
ReportResponse = _schemas_module.ReportResponse
ReportListResponse = _schemas_module.ReportListResponse
ReportJobStatusResponse = _schemas_module.ReportJobStatusResponse
EnhanceSectionRequest = _schemas_module.EnhanceSectionRequest
SuggestAssessmentRequest = _schemas_module.SuggestAssessmentRequest
UpdateReportRequest = _schemas_module.UpdateReportRequest
SubmitReportRequest = _schemas_module.SubmitReportRequest
AuditReadinessResponse = _schemas_module.AuditReadinessResponse
_constants_module = import_module("backend.20_ai.20_reports.constants")
get_report_service = _deps_module.get_report_service
ReportExportFormat = _constants_module.ReportExportFormat

router = InstrumentedAPIRouter(
    prefix="/api/v1/ai/reports",
    tags=["ai-reports"],
)


@router.post("", response_model=ReportResponse, status_code=201)
async def generate_report(
    payload: GenerateReportRequest,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    engagement_id: str | None = Query(None),
) -> ReportResponse:
    """
    Queue a new GRC report for AI generation.
    """
    return await service.generate_report(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
        engagement_id=engagement_id,
    )


@router.get("", response_model=ReportListResponse)
async def list_reports(
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    org_id: str | None = Query(None),
    report_type: str | None = Query(None),
    engagement_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ReportListResponse:
    """List reports for the current tenant, optionally filtered by org, type and engagement."""
    return await service.list_reports(
        tenant_key=claims.tenant_key,
        org_id=org_id,
        report_type=report_type,
        engagement_id=engagement_id,
        limit=limit,
        offset=offset,
    )


@router.get("/jobs/{job_id}/status", response_model=ReportJobStatusResponse)
async def get_job_status(
    job_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> ReportJobStatusResponse:
    """Poll generation job status."""
    return await service.get_job_status(
        job_id=job_id,
        tenant_key=claims.tenant_key,
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> ReportResponse:
    """Get a report by ID (includes full markdown content when completed)."""
    return await service.get_report(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        report_id=report_id,
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    fmt: ReportExportFormat = Query(
        ReportExportFormat.PDF, description="Export format: pdf, docx, or md"
    ),
) -> StreamingResponse:
    """Download a report in the specified format."""
    file_bytes, media_type, filename = await service.get_report_download(
        report_id=report_id,
        fmt=fmt,
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
    )

    return StreamingResponse(
        iter([file_bytes]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{report_id}/enhance-section")
async def enhance_report_section(
    report_id: str,
    body: EnhanceSectionRequest,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> StreamingResponse:
    """
    Stream AI-enhanced markdown for a single section of a completed report.

    Uses the same GRC context data as the original report generation.

    SSE event types:
      - content_delta:     {"delta": "<partial text>"}
      - enhance_complete:  {"enhance_id": "...", "section_title": "...", "enhanced_section": "...", "usage": {...}}
      - enhance_error:     {"enhance_id": "...", "error_code": "...", "message": "..."}
    """
    return StreamingResponse(
        service.stream_enhance_section(
            user_id=claims.subject,
            tenant_key=claims.tenant_key,
            report_id=report_id,
            request=body,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/{report_id}/suggest-assessment")
async def suggest_report_assessment(
    report_id: str,
    body: SuggestAssessmentRequest,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> StreamingResponse:
    """
    Stream an AI-generated assessment suggestion for a completed report.

    SSE event types:
      - content_delta:       {"delta": "<partial JSON token>"}
      - suggestion_complete: {"verdict": "...", "verdict_rationale": "...", "findings": [...]}
      - suggestion_error:    {"error_code": "...", "message": "..."}
    """
    return StreamingResponse(
        service.stream_suggest_assessment(
            user_id=claims.subject,
            tenant_key=claims.tenant_key,
            report_id=report_id,
            request=body,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.patch("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: str,
    payload: UpdateReportRequest,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> ReportResponse:
    """Update report title or content."""
    return await service.update_report(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        report_id=report_id,
        request=payload,
    )


@router.post("/{report_id}/submit", response_model=ReportResponse, status_code=200)
async def submit_report(
    report_id: str,
    payload: SubmitReportRequest,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> ReportResponse:
    """
    Submit/attach a report to an engagement.
    Updates report status to submitted and links it to the engagement.
    """
    return await service.submit_report(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        report_id=report_id,
        engagement_id=payload.engagement_id,
        submission_notes=payload.submission_notes,
    )


@router.post("/framework-readiness/generate-and-submit", response_model=ReportResponse, status_code=201)
async def generate_and_submit_framework_readiness_report(
    payload: SubmitReportRequest,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    org_id: str = Query(...),
    workspace_id: str | None = Query(None),
    framework_id: str | None = Query(None),
) -> ReportResponse:
    """
    Generate a framework readiness report and immediately submit it to an engagement.
    This is a convenience endpoint that combines report generation and submission in one call.
    """
    return await service.generate_and_submit_framework_readiness_report(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        engagement_id=payload.engagement_id,
        org_id=org_id,
        workspace_id=workspace_id,
        framework_id=framework_id,
        submission_notes=payload.submission_notes,
    )


@router.post("/manual-upload-and-submit", response_model=ReportResponse, status_code=201)
async def upload_manual_report(
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    file: UploadFile = File(...),
    engagement_id: str = Form(...),
    title: str = Form(...),
    org_id: str | None = Form(None),
    workspace_id: str | None = Form(None),
    submission_notes: str | None = Form(None),
) -> ReportResponse:
    """
    Upload a manual report file and immediately submit it to an engagement.
    """
    file_data = await file.read()
    return await service.upload_and_submit_manual_report(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        engagement_id=engagement_id,
        title=title,
        submission_notes=submission_notes,
        original_filename=file.filename or "manual_report.pdf",
        declared_content_type=file.content_type or "application/pdf",
        file_data=file_data,
    )


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> None:
    """Delete a report."""
    await service.delete_report(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        report_id=report_id,
    )


@router.get(
    "/framework/{framework_id}/audit-readiness", response_model=AuditReadinessResponse
)
async def get_audit_readiness(
    framework_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    org_id: str = Query(...),
) -> AuditReadinessResponse:
    """Get audit readiness metrics for a framework."""
    return await service.get_audit_readiness(
        framework_id=framework_id,
        org_id=org_id,
        tenant_key=claims.tenant_key,
    )


@router.get("/framework/{framework_id}", response_model=ReportListResponse)
async def list_framework_reports(
    framework_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ReportListResponse:
    """List reports associated with a specific framework."""
    return await service.list_reports_by_framework(
        tenant_key=claims.tenant_key,
        framework_id=framework_id,
        limit=limit,
        offset=offset,
    )


@router.get("/engagement/{engagement_id}", response_model=ReportListResponse)
async def list_engagement_reports(
    engagement_id: str,
    service: Annotated[ReportService, Depends(get_report_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ReportListResponse:
    """List reports associated with a specific audit engagement."""
    return await service.list_reports_by_engagement(
        tenant_key=claims.tenant_key,
        engagement_id=engagement_id,
        limit=limit,
        offset=offset,
    )

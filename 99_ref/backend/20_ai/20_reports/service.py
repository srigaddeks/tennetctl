"""
ReportService — business logic for GRC report generation and retrieval.
"""

from __future__ import annotations

import base64
import asyncio
import datetime
import io
import json
import os
import uuid
from importlib import import_module
from typing import AsyncIterator

import asyncpg

from ..constants import AIAuditEventType
from .constants import ReportExportFormat
from .models import ReportRecord
from .repository import ReportRepository

_org_repo_module = import_module("backend.03_auth_manage.07_orgs.repository")
OrgRepository = _org_repo_module.OrgRepository
_license_repo_module = import_module(
    "backend.03_auth_manage.14_license_profiles.repository"
)
LicenseProfileRepository = _license_repo_module.LicenseProfileRepository
_engagement_repo_module = import_module("backend.12_engagements.repository")
_engagement_service_module = import_module("backend.12_engagements.service")
_framework_repo_module = import_module("backend.05_grc_library.02_frameworks.repository")
EngagementRepository = _engagement_repo_module.EngagementRepository
EngagementService = _engagement_service_module.EngagementService
FrameworkRepository = _framework_repo_module.FrameworkRepository
from .schemas import (
    EnhanceSectionRequest,
    GenerateReportRequest,
    ReportJobStatusResponse,
    ReportListResponse,
    ReportResponse,
    ReportSummaryResponse,
    SuggestAssessmentRequest,
    UpdateReportRequest,
)

_logging_module = import_module("backend.01_core.logging_utils")
_time_module = import_module("backend.01_core.time_utils")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_streaming_module = import_module("backend.20_ai.02_conversations.streaming")
_factory_mod = import_module("backend.20_ai.14_llm_providers.factory")
_resolver_module = import_module("backend.20_ai.12_agent_config.resolver")
_agent_config_repo_module = import_module("backend.20_ai.12_agent_config.repository")
_cache_mod = import_module("backend.01_core.cache")
_dispatcher_mod = import_module("backend.20_ai.05_mcp.dispatcher")

_constants_module = import_module("backend.20_ai.20_reports.constants")
ReportExportFormat = _constants_module.ReportExportFormat
get_logger = _logging_module.get_logger
utc_now_sql = _time_module.utc_now_sql
NotFoundError = _errors_module.NotFoundError
AuthorizationError = _errors_module.AuthorizationError
ValidationError = _errors_module.ValidationError
require_permission = _perm_check_module.require_permission
sse_event = _streaming_module.sse_event
get_provider = _factory_mod.get_provider
AgentConfigResolver = _resolver_module.AgentConfigResolver
AgentConfigRepository = _agent_config_repo_module.AgentConfigRepository
NullCacheManager = _cache_mod.NullCacheManager
MCPToolDispatcher = _dispatcher_mod.MCPToolDispatcher
ToolContext = _dispatcher_mod.ToolContext

from .exporter import ReportExporterMixin
from .copilot import ReportCopilotMixin

_audit_module = import_module("backend.01_core.audit")
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter

_JOBS = '"20_ai"."45_fct_job_queue"'


def _to_summary_response(r: ReportRecord) -> ReportSummaryResponse:
    return ReportSummaryResponse(
        id=r.id,
        report_type=r.report_type,
        title=r.title,
        status_code=r.status_code,
        word_count=r.word_count,
        is_auto_generated=r.is_auto_generated,
        workspace_id=r.workspace_id,
        parameters_json=r.parameters_json,
        trigger_entity_type=r.trigger_entity_type,
        trigger_entity_id=r.trigger_entity_id,
        created_at=r.created_at,
        completed_at=r.completed_at,
    )


def _to_response(r: ReportRecord) -> ReportResponse:
    return ReportResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        workspace_id=r.workspace_id,
        report_type=r.report_type,
        status_code=r.status_code,
        title=r.title,
        parameters_json=r.parameters_json,
        content_markdown=r.content_markdown,
        word_count=r.word_count,
        token_count=r.token_count,
        generated_by_user_id=r.generated_by_user_id,
        job_id=r.job_id,
        error_message=r.error_message,
        is_auto_generated=r.is_auto_generated,
        trigger_entity_type=r.trigger_entity_type,
        trigger_entity_id=r.trigger_entity_id,
        created_at=r.created_at,
        completed_at=r.completed_at,
        updated_at=r.updated_at,
    )


class ReportService(ReportExporterMixin, ReportCopilotMixin):
    def __init__(self, *, settings, database_pool: asyncpg.Pool, cache) -> None:
        self._settings = settings
        self._pool = database_pool
        self._cache = cache
        self._repo = ReportRepository()
        self._org_repo = OrgRepository()
        self._license_repo = LicenseProfileRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.ai.reports.service")

        # Initialize attachment service for manual uploads
        _attachments_svc = import_module("backend.09_attachments.01_attachments.service")
        self._attachment_service = _attachments_svc.AttachmentService(
            database_pool=database_pool,
            settings=settings,
            cache=cache,
        )

    async def generate_report(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: GenerateReportRequest,
        engagement_id: str | None = None,
    ) -> ReportResponse:
        job_id = str(uuid.uuid4())
        
        # Merge engagement_id into parameters if provided
        params = request.parameters or {}
        if engagement_id:
            params["engagement_id"] = engagement_id

        async with self._pool.acquire() as conn:
            # Create report record in queued state
            report = await self._repo.create_report(
                conn,
                tenant_key=tenant_key,
                org_id=request.org_id,
                workspace_id=request.workspace_id,
                report_type=request.report_type,
                title=request.title,
                parameters_json=params,
                generated_by_user_id=user_id,
                job_id=job_id,
                trigger_entity_type="engagement" if engagement_id else None,
                trigger_entity_id=engagement_id,
            )

            # Enqueue job
            await conn.execute(
                f"""
                INSERT INTO {_JOBS}
                    (id, tenant_key, user_id, org_id, workspace_id,
                     agent_type_code, priority_code, status_code, job_type, input_json,
                     estimated_tokens, max_retries)
                VALUES ($1::uuid, $2, $3::uuid, $4::uuid, $5::uuid,
                        'report_generator', 'normal', 'queued', 'generate_report', $6::jsonb,
                        8000, 1)
                """,
                job_id,
                tenant_key,
                user_id,
                request.org_id,
                request.workspace_id,
                json.dumps(
                    {
                        "report_id": report.id,
                        "report_type": request.report_type,
                        "org_id": request.org_id,
                        "workspace_id": request.workspace_id,
                        "user_id": user_id,
                        "tenant_key": tenant_key,
                        "parameters": params,
                        "engagement_id": engagement_id,
                    }
                ),
            )

        self._logger.info(
            "report.queued",
            extra={
                "report_id": report.id,
                "job_id": job_id,
                "type": request.report_type,
            },
        )
        return _to_response(report)

    async def get_report(
        self,
        *,
        user_id: str,
        tenant_key: str,
        report_id: str,
    ) -> ReportResponse:
        async with self._pool.acquire() as conn:
            report = await self._repo.get_report(conn, report_id, tenant_key)
        if not report:
            raise NotFoundError(f"Report {report_id} not found")
        return _to_response(report)

    async def list_reports(
        self,
        *,
        tenant_key: str,
        org_id: str | None = None,
        report_type: str | None = None,
        engagement_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ReportListResponse:
        async with self._pool.acquire() as conn:
            items, total = await self._repo.list_reports(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                report_type=report_type,
                engagement_id=engagement_id,
                limit=limit,
                offset=offset,
            )
        return ReportListResponse(
            items=[_to_summary_response(r) for r in items],
            total=total,
        )

    async def delete_report(
        self,
        *,
        user_id: str,
        tenant_key: str,
        report_id: str,
    ) -> None:
        async with self._pool.acquire() as conn:
            report = await self._repo.get_report(conn, report_id, tenant_key)
            if not report:
                raise NotFoundError(f"Report {report_id} not found")
            await self._repo.delete_report(conn, report_id, tenant_key)

    async def update_report(
        self,
        *,
        user_id: str,
        tenant_key: str,
        report_id: str,
        request: UpdateReportRequest,
    ) -> ReportResponse:
        word_count = None
        if request.content_markdown is not None:
            word_count = len(request.content_markdown.split())

        async with self._pool.acquire() as connection:
            # Check existence and ownership before starting transaction
            existing_report = await self._repo.get_report(
                connection, report_id, tenant_key
            )
            if not existing_report:
                raise NotFoundError(f"Report {report_id} not found")

            async with connection.transaction():
                updated_report = await self._repo.update_report(
                    connection,
                    report_id=report_id,
                    tenant_key=tenant_key,
                    title=request.title,
                    content_markdown=request.content_markdown,
                    word_count=word_count,
                )

                # Record audit entry
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="report",
                        entity_id=report_id,
                        event_type=AIAuditEventType.REPORT_UPDATED,
                        event_category="ai",
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "title_updated": str(request.title is not None),
                            "content_updated": str(
                                request.content_markdown is not None
                            ),
                        },
                        occurred_at=utc_now_sql(),
                    ),
                )

        self._logger.info(
            "report.updated",
            extra={"report_id": report_id, "user_id": user_id},
        )
        return _to_response(updated_report)

    async def submit_report(
        self,
        *,
        user_id: str,
        tenant_key: str,
        report_id: str,
        engagement_id: str,
        submission_notes: str | None = None,
    ) -> ReportResponse:
        """
        Submit/attach a report to an engagement.
        Updates report status to submitted, links it to the engagement, and updates engagement status.
        """
        async with self._pool.acquire() as connection:
            # Check report existence
            existing_report = await self._repo.get_report(
                connection, report_id, tenant_key
            )
            if not existing_report:
                raise NotFoundError(f"Report {report_id} not found")

            async with connection.transaction():
                # Update report with engagement attachment via repo method
                submitted_report = await self._repo.update_report_submission(
                    connection,
                    report_id=report_id,
                    tenant_key=tenant_key,
                    engagement_id=engagement_id,
                )

                # Update engagement status to 'review' after report submission
                engagement_repo = EngagementRepository()
                now = datetime.datetime.utcnow()
                engagement_updated = await engagement_repo.update_engagement(
                    connection,
                    engagement_id,
                    tenant_key,
                    status_code="review",
                    updated_by=user_id,
                    now=now,
                )

                # Record audit entry for report submission
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="report",
                        entity_id=report_id,
                        event_type=AIAuditEventType.REPORT_SUBMITTED,
                        event_category="ai",
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "engagement_id": engagement_id,
                            "submission_notes": submission_notes or "",
                            "engagement_status_updated": str(engagement_updated),
                        },
                        occurred_at=utc_now_sql(),
                    ),
                )

                # Record audit entry for engagement status change
                if engagement_updated:
                    await self._audit_writer.write_entry(
                        connection,
                        AuditEntry(
                            id=str(uuid.uuid4()),
                            tenant_key=tenant_key,
                            entity_type="engagement",
                            entity_id=engagement_id,
                            event_type="engagement_status_changed",
                            event_category="engagement",
                            actor_id=user_id,
                            actor_type="user",
                            properties={
                                "previous_status": existing_report.trigger_entity_type or "unknown",
                                "new_status": "review",
                                "report_id": report_id,
                            },
                            occurred_at=utc_now_sql(),
                        ),
                    )
            
            # Fetch final report state within connection context
            report = await self._repo.get_report(connection, report_id, tenant_key)

        self._logger.info(
            "report.submitted",
            extra={
                "report_id": report_id,
                "engagement_id": engagement_id,
                "user_id": user_id,
                "engagement_status_updated": engagement_updated,
            },
        )
        return _to_response(report)

    async def upload_and_submit_manual_report(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None,
        workspace_id: str | None,
        engagement_id: str,
        title: str,
        submission_notes: str | None = None,
        original_filename: str,
        declared_content_type: str,
        file_data: bytes,
    ) -> ReportResponse:
        """
        Uploads a manual report file as an attachment and creates/submits a report record.
        """
        async with self._pool.acquire() as connection:
            async with connection.transaction():
                # 1. Upload the file as an attachment linked to the engagement
                attachment = await self._attachment_service.upload_attachment(
                    user_id=user_id,
                    tenant_key=tenant_key,
                    portal_mode="auditor",
                    entity_type="engagement",
                    entity_id=engagement_id,
                    description=f"Manual report submission: {title}",
                    original_filename=original_filename,
                    declared_content_type=declared_content_type,
                    file_data=file_data,
                    org_id=org_id,
                    workspace_id=workspace_id,
                )

                # 2. Create the Report record
                report = await self._repo.create_report(
                    connection,
                    tenant_key=tenant_key,
                    org_id=org_id,
                    workspace_id=workspace_id,
                    report_type="manual_upload",
                    title=title,
                    parameters_json={
                        "attachment_id": attachment.id,
                        "engagement_id": engagement_id,
                        "original_filename": original_filename,
                        "submission_notes": submission_notes,
                    },
                    generated_by_user_id=user_id,
                    job_id=None,
                    trigger_entity_type="engagement",
                    trigger_entity_id=engagement_id,
                    is_auto_generated=False,
                )

                # 3. Mark the report as completed (since it's a manual upload)
                await self._repo.update_report_content(
                    connection,
                    report.id,
                    markdown_content=f"Manually uploaded report: {original_filename}. See attachments.",
                    word_count=0,
                    token_count=0,
                )

                # Update status and link to engagement
                submitted_report = await self._repo.update_report_submission(
                    connection,
                    report_id=report.id,
                    tenant_key=tenant_key,
                    engagement_id=engagement_id,
                )

                # 4. Update engagement status to 'review'
                engagement_repo = EngagementRepository()
                now = datetime.datetime.utcnow()
                engagement_updated = await engagement_repo.update_engagement(
                    connection,
                    engagement_id,
                    tenant_key,
                    status_code="review",
                    updated_by=user_id,
                    now=now,
                )

                # 5. Record audit entries
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="report",
                        entity_id=report.id,
                        event_type=AIAuditEventType.REPORT_SUBMITTED,
                        event_category="ai",
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "engagement_id": engagement_id,
                            "submission_notes": submission_notes or "",
                            "attachment_id": attachment.id,
                            "manual_upload": "true",
                        },
                        occurred_at=utc_now_sql(),
                    ),
                )

                if engagement_updated:
                    await self._audit_writer.write_entry(
                        connection,
                        AuditEntry(
                            id=str(uuid.uuid4()),
                            tenant_key=tenant_key,
                            entity_type="engagement",
                            entity_id=engagement_id,
                            event_type="engagement_status_changed",
                            event_category="engagement",
                            actor_id=user_id,
                            actor_type="user",
                            properties={
                                "new_status": "review",
                                "reason": "manual_report_submission",
                            },
                            occurred_at=utc_now_sql(),
                        ),
                    )

                return _to_response(submitted_report)

    async def generate_and_submit_framework_readiness_report(
        self,
        *,
        user_id: str,
        tenant_key: str,
        engagement_id: str,
        org_id: str,
        workspace_id: str | None = None,
        framework_id: str | None = None,
        submission_notes: str | None = None,
    ) -> ReportResponse:
        """
        Generate a framework readiness report and immediately submit it to an engagement.
        This is a convenience method combining report generation and submission.
        """
        # Fetch engagement and framework details for a meaningful report title
        engagement_name = "Unknown Engagement"
        framework_name = "Unknown Framework"
        
        async with self._pool.acquire() as conn:
            # Fetch engagement name
            engagement_repo = EngagementRepository()
            engagement = await engagement_repo.get_engagement_by_id(
                conn,
                engagement_id,
                tenant_key,
            )
            if engagement:
                engagement_name = engagement.engagement_name or "Unknown Engagement"
            
            # Fetch framework name
            if framework_id:
                framework_repo = FrameworkRepository()
                framework = await framework_repo.get_framework_by_id(
                    conn,
                    framework_id,
                )
                if framework:
                    framework_name = framework.name or "Unknown Framework"
        
        # Create report title with engagement and framework names
        report_title = f"Framework Readiness Report - {engagement_name} ({framework_name})"
        
        # Step 1: Generate the framework readiness report
        generate_req = GenerateReportRequest(
            org_id=org_id,
            workspace_id=workspace_id,
            report_type="framework_readiness",
            title=report_title,
            parameters={
                "engagement_id": engagement_id,
                "framework_id": framework_id,
            },
        )
        
        report_resp = await self.generate_report(
            user_id=user_id,
            tenant_key=tenant_key,
            request=generate_req,
            engagement_id=engagement_id,
        )
        
        # Step 2: Submit the generated report to the engagement
        submitted = await self.submit_report(
            user_id=user_id,
            tenant_key=tenant_key,
            report_id=report_resp.id,
            engagement_id=engagement_id,
            submission_notes=submission_notes or "Auto-generated framework readiness report",
        )
        
        self._logger.info(
            "framework_readiness_report.generated_and_submitted",
            extra={
                "report_id": submitted.id,
                "engagement_id": engagement_id,
                "engagement_name": engagement_name,
                "framework_id": framework_id,
                "framework_name": framework_name,
                "user_id": user_id,
            },
        )
        return submitted

    async def get_report_download(
        self,
        *,
        report_id: str,
        fmt: str,
        user_id: str,
        tenant_key: str,
    ) -> tuple[bytes, str, str]:
        """
        Export a report in the requested format.
        Returns (bytes, media_type, filename).
        """
        async with self._pool.acquire() as conn:
            report = await self._repo.get_report(conn, report_id, tenant_key)
            if not report:
                raise NotFoundError(f"Report {report_id} not found")
            
            # Check if report content is available
            if not report.content_markdown:
                raise ValidationError(
                    f"Report content is not yet available. Current status: {report.status_code}. "
                    "Please wait for the report generation to complete."
                )

            # Conditional watermark logic based on Org Type
            show_watermark = False
            watermark_image_path = None
            if report.org_id:
                org = await self._org_repo.get_org_by_id(conn, report.org_id)
                profile = await self._license_repo.get_profile_for_org(
                    conn, report.org_id
                )
                tier = profile["tier"] if profile else "free"

                if tier == "free":
                    show_watermark = True
                    # Use kreesalis.png icon from the same directory
                    logo_path = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), "kreesalis.png"
                    )
                    watermark_image_path = self._prepare_watermark(
                        logo_path, report.org_id
                    )

        content = report.content_markdown
        title_stem = (report.title or "Report").replace(" ", "_").lower()

        if fmt == ReportExportFormat.MD:
            return content.encode("utf-8"), "text/markdown", f"{title_stem}.md"

        if fmt == ReportExportFormat.PDF:
            pdf_bytes = await self._convert_to_pdf(
                content,
                report.title or "GRC Report",
                show_watermark=show_watermark,
                watermark_path=watermark_image_path,
            )
            return pdf_bytes, "application/pdf", f"{title_stem}.pdf"

        if fmt == ReportExportFormat.DOCX:
            docx_bytes = await self._convert_to_docx(
                content,
                report.title or "GRC Report",
                show_watermark=show_watermark,
                watermark_path=watermark_image_path,
            )
            return (
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                f"{title_stem}.docx",
            )

        raise ValidationError(f"Unsupported export format: {fmt}")

    async def download_markdown(
        self,
        *,
        user_id: str,
        tenant_key: str,
        report_id: str,
    ) -> tuple[str, bytes]:
        async with self._pool.acquire() as conn:
            report = await self._repo.get_report(conn, report_id, tenant_key)
        if not report:
            raise NotFoundError(f"Report {report_id} not found")
        if not report.content_markdown:
            raise NotFoundError("Report content not yet available")
        slug = (report.title or report.report_type).lower().replace(" ", "_")[:40]
        filename = f"kcontrol_{report.report_type}_{report.id[:8]}_{slug}.md"
        return filename, report.content_markdown.encode("utf-8")

    async def get_job_status(
        self,
        *,
        job_id: str,
        tenant_key: str,
    ) -> ReportJobStatusResponse:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT id::text, status_code, error_message,
                       started_at::text, completed_at::text, created_at::text
                FROM {_JOBS}
                WHERE id = $1::uuid AND tenant_key = $2
                """,
                job_id,
                tenant_key,
            )
            if not row:
                raise NotFoundError(f"Job {job_id} not found")
            # Find linked report
            report = await self._repo.get_report_by_job(conn, job_id)

        return ReportJobStatusResponse(
            job_id=row["id"],
            report_id=report.id if report else None,
            status_code=row["status_code"],
            error_message=row["error_message"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            created_at=row["created_at"],
        )

    async def list_reports_by_framework(
        self,
        *,
        tenant_key: str,
        framework_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> ReportListResponse:
        async with self._pool.acquire() as conn:
            items, total = await self._repo.list_reports_by_framework(
                conn,
                tenant_key=tenant_key,
                framework_id=framework_id,
                limit=limit,
                offset=offset,
            )
        return ReportListResponse(
            items=[_to_summary_response(r) for r in items],
            total=total,
        )

    async def list_reports_by_engagement(
        self,
        *,
        tenant_key: str,
        engagement_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> ReportListResponse:
        async with self._pool.acquire() as conn:
            items, total = await self._repo.list_reports_by_engagement(
                conn,
                tenant_key=tenant_key,
                engagement_id=engagement_id,
                limit=limit,
                offset=offset,
            )
        return ReportListResponse(
            items=[_to_summary_response(r) for r in items],
            total=total,
        )

    async def get_audit_readiness(
        self,
        *,
        framework_id: str,
        org_id: str,
        tenant_key: str,
    ):
        from .schemas import (
            AuditReadinessResponse,
            AuditReadinessControls,
            AuditReadinessEvidence,
        )

        _GRC_SCHEMA = '"05_grc_library"'
        _TASKS_SCHEMA = '"08_tasks"'

        async with self._pool.acquire() as conn:
            # Total controls for this framework
            control_row = await conn.fetchrow(
                f"""
                SELECT COUNT(*)::int AS total,
                       COUNT(*) FILTER (WHERE test_count > 0)::int AS with_tests
                FROM {_GRC_SCHEMA}."41_vw_control_detail"
                WHERE framework_id = $1::uuid AND is_deleted = FALSE
                """,
                framework_id,
            )
            total_controls = control_row["total"] if control_row else 0
            controls_with_tests = control_row["with_tests"] if control_row else 0

            # Evidence tasks for this framework's controls
            evidence_row = await conn.fetchrow(
                f"""
                SELECT COUNT(*)::int AS total,
                       COUNT(*) FILTER (WHERE status_code = 'completed')::int AS complete
                FROM {_TASKS_SCHEMA}."10_fct_tasks"
                WHERE entity_type = 'control'
                  AND entity_id IN (
                    SELECT id FROM {_GRC_SCHEMA}."13_fct_controls"
                    WHERE framework_id = $1::uuid AND is_deleted = FALSE
                  )
                  AND task_type_code = 'evidence_collection'
                  AND is_deleted = FALSE
                """,
                framework_id,
            )
            total_evidence = evidence_row["total"] if evidence_row else 0
            complete_evidence = evidence_row["complete"] if evidence_row else 0

            # Open gaps = controls without tests
            open_gaps = total_controls - controls_with_tests

            # Calculate readiness percentage
            # 40% controls passing, 40% evidence complete, 20% no gaps
            controls_pct = (
                (controls_with_tests / total_controls * 100)
                if total_controls > 0
                else 0
            )
            evidence_pct = (
                (complete_evidence / total_evidence * 100)
                if total_evidence > 0
                else 100
            )
            gaps_pct = (
                100
                if total_controls == 0
                else ((total_controls - open_gaps) / total_controls * 100)
            )
            readiness_pct = round(
                controls_pct * 0.4 + evidence_pct * 0.4 + gaps_pct * 0.2, 1
            )

            # Auditor access - check if any user in the org has a group with an auditor/viewer role
            auditor_row = await conn.fetchrow(
                f"""
                SELECT COUNT(*)::int AS cnt
                FROM "03_auth_manage"."18_lnk_group_memberships" gm
                JOIN "03_auth_manage"."17_fct_user_groups" g ON g.id = gm.group_id
                JOIN "03_auth_manage"."19_lnk_group_role_assignments" gra ON gra.group_id = gm.group_id
                JOIN "03_auth_manage"."16_fct_roles" r ON r.id = gra.role_id
                WHERE g.scope_org_id = $1::uuid
                  AND r.code IN ('auditor', 'viewer')
                  AND gm.is_active = TRUE AND gm.is_deleted = FALSE
                  AND g.is_active = TRUE AND g.is_deleted = FALSE
                  AND gra.is_active = TRUE AND gra.is_deleted = FALSE
                  AND r.is_deleted = FALSE
                LIMIT 1
                """,
                org_id,
            )
            auditor_count = auditor_row["cnt"] if auditor_row else 0
            auditor_access = "Active" if auditor_count > 0 else "Inactive"

        return AuditReadinessResponse(
            framework_id=framework_id,
            controls_passing=AuditReadinessControls(
                passed=controls_with_tests,
                total=total_controls,
            ),
            evidence_complete=AuditReadinessEvidence(
                complete=complete_evidence,
                total=total_evidence,
            ),
            open_gaps=open_gaps,
            auditor_access=auditor_access,
            readiness_pct=readiness_pct,
        )

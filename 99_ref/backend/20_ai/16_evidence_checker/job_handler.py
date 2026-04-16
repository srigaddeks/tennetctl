"""
Job handler for evidence_check jobs.

The existing job queue worker calls handle_evidence_check_job() when it picks
up a job with job_type='evidence_check'.

Flow:
  1. Load job input from job queue record (task_id, attachment_ids, etc.)
  2. transition: queued → ingesting  (DB + SSE)
  3. For each attachment: run ingestion pipeline (idempotent)
  4. transition: ingesting → evaluating  (DB + SSE)
  5. Run EvidenceLeadAgent — fires on_criterion_done callback after each criterion
  6. On success: write report to DB → transition → completed → notification
  7. On failure: transition → failed + emit SSE error event

Sequential job concurrency is enforced by the job queue worker (max_concurrent_jobs
in 44_fct_agent_rate_limits for agent_type_code='evidence_lead'), not here.
This handler does NOT need to know about that; it just processes the single job
it receives.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from importlib import import_module

import asyncpg

from .evidence_lead_agent import EvidenceLeadAgent
from .ingestion import delete_collection, index_attachment
from .models import IngestionResult
from .report_generator import generate_markdown_report
from .repository import EvidenceCheckerRepository

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.evidence_checker.job_handler")

_DEFAULT_PAGE_CAP = int(os.getenv("EVIDENCE_CHECKER_PAGE_CAP", "10000"))

# SSE helper — reuse existing streaming module
_streaming_module = import_module("backend.20_ai.02_conversations.streaming")
_sse_event = _streaming_module.sse_event


async def _emit_sse(event_type: str, payload: dict, task_id: str, settings) -> None:
    """
    Emit a task-scoped SSE event.
    Uses the existing SSE broadcast mechanism on the task channel.
    """
    try:
        _sse_broadcast = import_module("backend.01_core.sse_bus").broadcast
        await _sse_broadcast(
            channel=f"task:{task_id}",
            event=event_type,
            data=payload,
        )
    except Exception as exc:
        _logger.debug("SSE emit failed (non-fatal): %s", exc)


async def _fetch_attachment_file(attachment_id: str, pool: asyncpg.Pool) -> tuple[bytes, str, str]:
    """
    Return (file_data, document_filename, mime_type) for an attachment.
    Reads from the existing task attachment + file storage tables.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT original_filename AS filename, content_type AS mime_type, storage_key AS s3_key, storage_provider AS storage_backend
            FROM "09_attachments"."01_fct_attachments"
            WHERE id = $1::uuid AND is_deleted = FALSE
            """,
            attachment_id,
        )

    if not row:
        raise FileNotFoundError(f"Attachment {attachment_id} not found or deleted")

    filename = row["filename"] or "unknown"
    mime_type = row["mime_type"] or "application/octet-stream"
    s3_key = row["s3_key"]
    storage_backend = row["storage_backend"]

    # Pull file bytes from storage using a presigned URL
    _storage_factory = import_module("backend.09_attachments.storage.factory")
    _settings = import_module("backend.00_config.settings").load_settings()
    provider = _storage_factory.get_storage_provider(_settings)
    
    url_result = await provider.generate_presigned_download_url(
        storage_key=s3_key,
        filename=filename,
    )
    
    import httpx
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.get(url_result.url)
        resp.raise_for_status()
        file_data = resp.content
        
    return file_data, filename, mime_type


def _build_qdrant_client(settings):
    """Build a real synchronous Qdrant client from settings. Never mocked."""
    try:
        from qdrant_client import QdrantClient
    except ImportError:
        raise RuntimeError("qdrant-client package not installed. Add it to requirements.")

    qdrant_url = (
        getattr(settings, "qdrant_url", None)
        or getattr(settings, "ai_qdrant_url", None)
        or os.getenv("QDRANT_URL", "")
        or os.getenv("AI_QDRANT_URL", "")
    )
    if not qdrant_url:
        raise RuntimeError(
            "Qdrant URL is not configured. Set QDRANT_URL (or AI_QDRANT_URL) env var "
            "to your Qdrant instance. Evidence checking requires a real Qdrant instance."
        )

    qdrant_api_key = (
        getattr(settings, "qdrant_api_key", None)
        or getattr(settings, "ai_qdrant_api_key", None)
        or os.getenv("QDRANT_API_KEY", "")
        or os.getenv("AI_QDRANT_API_KEY", "")
        or None
    )

    port = 443 if qdrant_url.startswith("https://") else 6333
    return QdrantClient(url=qdrant_url, port=port, api_key=qdrant_api_key, timeout=60.0)


async def handle_evidence_check_job(
    job,  # JobRecord from 15_job_queue
    pool: asyncpg.Pool,
    settings,
) -> None:
    """
    Main entry point called by the job queue worker for job_type='evidence_check'.

    job.input_json expected shape:
    {
      "task_id": "<uuid>",
      "org_id": "<uuid>",
      "tenant_key": "<str>",
      "triggered_by_attachment_id": "<uuid | null>",
      "attachment_ids": ["<uuid>", ...],
      "page_cap": 10000
    }
    """
    repo = EvidenceCheckerRepository()
    job_input = job.input_json if isinstance(job.input_json, dict) else json.loads(job.input_json)

    task_id: str = job_input["task_id"]
    org_id: str = job_input["org_id"]
    tenant_key: str = job_input["tenant_key"]
    attachment_ids: list[str] = job_input.get("attachment_ids", [])
    page_cap: int = job_input.get("page_cap", _DEFAULT_PAGE_CAP)

    internal_job_id: str = job_input.get("evidence_job_id", str(uuid.uuid4()))

    _logger.info(
        "evidence_check.job_started",
        extra={
            "job_id": job.id, "evidence_job_id": internal_job_id,
            "task_id": task_id, "org_id": org_id,
            "attachment_count": len(attachment_ids),
        },
    )

    try:
        # ── PHASE 1: ingesting ───────────────────────────────────────────────
        async with pool.acquire() as conn:
            await repo.update_job_status(conn, job_id=internal_job_id, status_code="ingesting")

        await _emit_sse("evidence_check_status", {
            "task_id": task_id, "job_id": internal_job_id,
            "status": "ingesting", "attachment_count": len(attachment_ids),
        }, task_id, settings)

        qdrant_client = _build_qdrant_client(settings)

        ingestion_results: list[IngestionResult] = []
        total_pages = 0

        # Resolve the checker provider for ingestion (needed for vision + embedding)
        from .evidence_lead_agent import _resolve_checker_config
        provider = await _resolve_checker_config(pool, org_id, settings)

        for att_id in attachment_ids:
            try:
                file_data, filename, mime_type = await _fetch_attachment_file(att_id, pool)
                result = await index_attachment(
                    task_id=task_id,
                    org_id=org_id,
                    attachment_id=att_id,
                    document_filename=filename,
                    file_data=file_data,
                    mime_type=mime_type,
                    page_cap=page_cap,
                    llm_provider=provider,
                    qdrant_client=qdrant_client,
                )
                ingestion_results.append(result)
                total_pages += result.pages_processed
            except Exception as exc:
                _logger.warning("Ingestion failed for attachment %s: %s", att_id, exc)
                ingestion_results.append(
                    IngestionResult(attachment_id=att_id, pages_processed=0, chunks_indexed=0, error=str(exc))
                )

        async with pool.acquire() as conn:
            await repo.update_job_status(
                conn, job_id=internal_job_id,
                status_code="evaluating",
                pages_analyzed=total_pages,
            )

        await _emit_sse("evidence_check_status", {
            "task_id": task_id, "job_id": internal_job_id,
            "status": "evaluating", "pages_analyzed": total_pages,
        }, task_id, settings)

        # ── PHASE 2: evaluating ──────────────────────────────────────────────
        # Count total criteria ahead of fan-out so we can show a total
        from .evidence_lead_agent import _load_criteria
        criteria = await _load_criteria(pool, task_id)
        criteria_total = len(criteria)

        async with pool.acquire() as conn:
            await repo.update_job_status(
                conn, job_id=internal_job_id,
                status_code="evaluating",
                criteria_total=criteria_total,
            )

        criteria_done_counter = 0

        async def on_criterion_done(result, done_count, total_count):
            nonlocal criteria_done_counter
            criteria_done_counter = done_count
            async with pool.acquire() as conn:
                await repo.update_job_status(
                    conn, job_id=internal_job_id,
                    status_code="evaluating",
                    criteria_done=done_count,
                    criteria_total=total_count,
                )
            await _emit_sse("evidence_check_progress", {
                "task_id": task_id, "job_id": internal_job_id,
                "criteria_done": done_count,
                "criteria_total": total_count,
                "last_verdict": result.verdict,
            }, task_id, settings)

        lead = EvidenceLeadAgent(pool=pool, settings=settings, qdrant_client=qdrant_client)
        report = await lead.run(
            task_id=task_id,
            org_id=org_id,
            job_id=internal_job_id,
            attachment_ids=attachment_ids,
            on_criterion_done=on_criterion_done,
        )
        report.total_pages_analyzed = total_pages

        # ── PHASE 3: write report + complete ────────────────────────────────
        # Fetch task title for the markdown report (best-effort)
        task_title: str | None = None
        task_description: str | None = None
        try:
            async with pool.acquire() as conn:
                title_row = await conn.fetchrow(
                    """
                    SELECT property_value
                    FROM "08_tasks"."20_dtl_task_properties"
                    WHERE task_id = $1::uuid AND property_key = 'title'
                    """,
                    task_id,
                )
                if title_row:
                    task_title = title_row["property_value"]
                desc_row = await conn.fetchrow(
                    """
                    SELECT property_value
                    FROM "08_tasks"."20_dtl_task_properties"
                    WHERE task_id = $1::uuid AND property_key = 'description'
                    """,
                    task_id,
                )
                if desc_row:
                    task_description = desc_row["property_value"]
        except Exception as exc:
            _logger.debug("Could not fetch task title for markdown report: %s", exc)

        markdown_report = generate_markdown_report(
            report,
            task_title=task_title,
            task_description=task_description,
        )

        async with pool.acquire() as conn:
            async with conn.transaction():
                report_id = await repo.write_report(
                    conn,
                    report=report,
                    tenant_key=tenant_key,
                    org_id=org_id,
                    markdown_report=markdown_report,
                )
                await repo.update_job_status(
                    conn, job_id=internal_job_id,
                    status_code="completed",
                    criteria_done=criteria_done_counter,
                    pages_analyzed=total_pages,
                )

        await _emit_sse("evidence_check_done", {
            "task_id": task_id, "job_id": internal_job_id,
            "report_id": report_id,
            "overall_verdict": report.overall_verdict,
            "met_count": sum(1 for r in report.criteria_results if r.verdict == "MET"),
            "total_count": criteria_done_counter,
        }, task_id, settings)

        # ── Notify assignees ──────────────────────────────────────────────────
        await _notify_task_users(pool, task_id, org_id, report.overall_verdict, criteria_done_counter)

        _logger.info(
            "evidence_check.job_completed",
            extra={
                "job_id": job.id, "evidence_job_id": internal_job_id,
                "task_id": task_id, "overall_verdict": report.overall_verdict,
                "duration_s": report.duration_seconds, "report_id": report_id,
            },
        )

    except Exception as exc:
        _logger.exception("evidence_check.job_failed: %s", exc)
        async with pool.acquire() as conn:
            await repo.update_job_status(
                conn, job_id=internal_job_id,
                status_code="failed",
                error_message=str(exc)[:2000],
            )
        await _emit_sse("evidence_check_failed", {
            "task_id": task_id, "job_id": internal_job_id,
            "error": str(exc)[:300],
        }, task_id, settings)
        raise  # re-raise so the job queue marks the outer 45_fct_job_queue row as failed


async def enqueue_evidence_check(
    *,
    pool: asyncpg.Pool,
    tenant_key: str,
    org_id: str,
    task_id: str,
    triggered_by_attachment_id: str | None,
    attachment_ids: list[str],
    user_id: str,
    page_cap: int = _DEFAULT_PAGE_CAP,
) -> str:
    """
    Public entry point called when a new attachment is uploaded to a task.

    1. Creates a row in 70_fct_evidence_check_jobs (internal tracking)
    2. Supersedes any existing queued/running jobs for this task
    3. Enqueues into 45_fct_job_queue (existing) with job_type='evidence_check'

    Returns the 45_fct_job_queue job ID.
    """
    _jq_repo_mod = import_module("backend.20_ai.15_job_queue.repository")
    JobQueueRepository = _jq_repo_mod.JobQueueRepository

    repo = EvidenceCheckerRepository()
    jq_repo = JobQueueRepository()

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Supersede any active jobs for this task
            superseded = await repo.supersede_active_jobs(
                conn, task_id=task_id, tenant_key=tenant_key
            )
            if superseded:
                _logger.info("Superseded %d existing evidence jobs for task %s", len(superseded), task_id)

            # Create internal job tracking row
            evidence_job_id = await repo.create_job(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                task_id=task_id,
                triggered_by_attachment_id=triggered_by_attachment_id,
                attachment_ids=attachment_ids,
                page_cap=page_cap,
            )

            # Recompute queue positions
            await repo.update_queue_positions(conn, tenant_key=tenant_key)

            # Enqueue into the existing job queue
            job_record = await jq_repo.enqueue_job(
                conn,
                tenant_key=tenant_key,
                user_id=user_id,
                org_id=org_id,
                workspace_id=None,
                agent_type_code="evidence_lead",
                priority_code="normal",
                job_type="evidence_check",
                input_json={
                    "task_id": task_id,
                    "org_id": org_id,
                    "tenant_key": tenant_key,
                    "triggered_by_attachment_id": triggered_by_attachment_id,
                    "attachment_ids": attachment_ids,
                    "page_cap": page_cap,
                    "evidence_job_id": evidence_job_id,
                },
                estimated_tokens=2000 * len(attachment_ids),  # rough estimate
                scheduled_at=None,
                max_retries=2,
                conversation_id=None,
                batch_id=None,
            )

    _logger.info(
        "evidence_check.enqueued",
        extra={
            "job_queue_id": job_record.id, "evidence_job_id": evidence_job_id,
            "task_id": task_id, "attachment_count": len(attachment_ids),
        },
    )
    return job_record.id


async def _notify_task_users(pool: asyncpg.Pool, task_id: str, org_id: str, overall_verdict: str, criteria_count: int) -> None:
    """Send an in-app notification to task assignees on evaluation completion."""
    try:
        _notification = import_module("backend.06_notifications.service")
        met_label = "All met" if overall_verdict == "ALL_MET" else overall_verdict.replace("_", " ").title()
        await _notification.create_system_notification(
            pool=pool,
            entity_type="task",
            entity_id=task_id,
            org_id=org_id,
            event_key="evidence_check_completed",
            message=f"Evidence check completed — {met_label} ({criteria_count} criteria evaluated)",
        )
    except Exception as exc:
        _logger.debug("Notification send failed (non-fatal): %s", exc)

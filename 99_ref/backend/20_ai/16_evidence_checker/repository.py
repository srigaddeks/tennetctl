"""
EvidenceCheckerRepository — all DB persistence for the Evidence Checker feature.

Uses the existing schema "20_ai" and the three tables added in the migration:
  70_fct_evidence_check_jobs     — job lifecycle tracking
  71_fct_evidence_check_reports  — one report per completed evaluation
  72_fct_evidence_criteria_results — per-criterion verdicts

All writes are factual; audit events are emitted by the service layer.
"""

from __future__ import annotations

import json
from typing import Any

import asyncpg

from importlib import import_module

from .models import CriterionResult, EvidenceReference, EvidenceReport

_SCHEMA = '"20_ai"'
_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.evidence_checker.repository")
_JOBS = f'{_SCHEMA}."70_fct_evidence_check_jobs"'
_REPORTS = f'{_SCHEMA}."71_fct_evidence_check_reports"'
_CRITERIA = f'{_SCHEMA}."72_fct_evidence_criteria_results"'


def _ref_to_dict(r: EvidenceReference) -> dict:
    return {
        "document_filename": r.document_filename,
        "page_number": r.page_number,
        "section_or_sheet": r.section_or_sheet,
        "excerpt": r.excerpt[:150],
        "confidence": round(r.confidence, 4),
    }


class EvidenceCheckerRepository:

    # ── Job lifecycle ────────────────────────────────────────────────────────

    async def create_job(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str,
        task_id: str,
        triggered_by_attachment_id: str | None,
        attachment_ids: list[str],
        page_cap: int,
    ) -> str:
        """Insert a new evidence_check_job row, return job_id (str UUID)."""
        row = await conn.fetchrow(
            f"""
            INSERT INTO {_JOBS}
                (tenant_key, org_id, task_id, triggered_by_attachment_id,
                 attachment_ids, page_cap)
            VALUES ($1, $2::uuid, $3::uuid, $4::uuid, $5, $6)
            RETURNING id::text
            """,
            tenant_key, org_id, task_id, triggered_by_attachment_id,
            json.dumps(attachment_ids), page_cap,
        )
        return row["id"]

    async def update_job_status(
        self,
        conn: asyncpg.Connection,
        *,
        job_id: str,
        status_code: str,
        criteria_done: int | None = None,
        criteria_total: int | None = None,
        pages_analyzed: int | None = None,
        error_message: str | None = None,
    ) -> None:
        sets = ["status_code = $2", "updated_at = NOW()"]
        params: list[Any] = [job_id, status_code]
        idx = 3
        if status_code in ("ingesting", "evaluating", "running"):
            sets.append("started_at = COALESCE(started_at, NOW())")
        if status_code in ("completed", "failed", "cancelled", "superseded"):
            sets.append("completed_at = NOW()")
        if criteria_done is not None:
            sets.append(f"progress_criteria_done = ${idx}"); params.append(criteria_done); idx += 1
        if criteria_total is not None:
            sets.append(f"progress_criteria_total = ${idx}"); params.append(criteria_total); idx += 1
        if pages_analyzed is not None:
            sets.append(f"pages_analyzed = ${idx}"); params.append(pages_analyzed); idx += 1
        if error_message is not None:
            sets.append(f"error_message = ${idx}"); params.append(error_message); idx += 1

        await conn.execute(
            f"UPDATE {_JOBS} SET {', '.join(sets)} WHERE id = $1::uuid",
            *params,
        )

    async def supersede_active_jobs(
        self,
        conn: asyncpg.Connection,
        *,
        task_id: str,
        tenant_key: str,
    ) -> list[str]:
        """Mark any queued/running jobs for this task as superseded. Returns their IDs."""
        rows = await conn.fetch(
            f"""
            UPDATE {_JOBS}
            SET status_code = 'superseded', completed_at = NOW(), updated_at = NOW()
            WHERE task_id = $1::uuid
              AND tenant_key = $2
              AND status_code IN ('queued', 'ingesting', 'evaluating')
              AND is_deleted = FALSE
            RETURNING id::text
            """,
            task_id, tenant_key,
        )
        return [r["id"] for r in rows]

    async def get_current_job(
        self,
        conn: asyncpg.Connection,
        *,
        task_id: str,
        tenant_key: str,
    ) -> dict | None:
        row = await conn.fetchrow(
            f"""
            SELECT id::text, status_code, queue_position, estimated_wait_seconds,
                   progress_criteria_done, progress_criteria_total,
                   pages_analyzed, error_message,
                   started_at::text, completed_at::text, created_at::text
            FROM {_JOBS}
            WHERE task_id = $1::uuid AND tenant_key = $2
              AND is_deleted = FALSE
            ORDER BY created_at DESC LIMIT 1
            """,
            task_id, tenant_key,
        )
        return dict(row) if row else None

    async def update_queue_positions(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
    ) -> None:
        """Recompute queue_position for all queued evidence_check jobs in this tenant."""
        await conn.execute(
            f"""
            WITH ranked AS (
                SELECT id,
                       ROW_NUMBER() OVER (ORDER BY created_at) AS pos
                FROM {_JOBS}
                WHERE tenant_key = $1
                  AND status_code = 'queued'
                  AND is_deleted = FALSE
            )
            UPDATE {_JOBS} j
            SET queue_position = r.pos,
                updated_at = NOW()
            FROM ranked r WHERE j.id = r.id
            """,
            tenant_key,
        )

    # ── Report persistence ───────────────────────────────────────────────────

    async def write_report(
        self,
        conn: asyncpg.Connection,
        *,
        report: EvidenceReport,
        tenant_key: str,
        org_id: str,
        markdown_report: str | None = None,
    ) -> str:
        """Write report + criteria results in a single transaction. Returns report_id."""
        # Deactivate previous reports for this task
        await conn.execute(
            f"""
            UPDATE {_REPORTS}
            SET is_active = FALSE, updated_at = NOW()
            WHERE task_id = $1::uuid AND is_active = TRUE AND is_deleted = FALSE
            """,
            report.task_id,
        )

        # Determine next version number
        row = await conn.fetchrow(
            f"SELECT COALESCE(MAX(version), 0) + 1 AS nv FROM {_REPORTS} WHERE task_id = $1::uuid",
            report.task_id,
        )
        version = int(row["nv"])

        # Insert report
        report_row = await conn.fetchrow(
            f"""
            INSERT INTO {_REPORTS}
                (tenant_key, org_id, task_id, job_id, version, is_active,
                 overall_verdict, attachment_count, total_pages_analyzed,
                 langfuse_trace_id, tokens_consumed, duration_seconds,
                 markdown_report)
            VALUES ($1, $2::uuid, $3::uuid, $4::uuid, $5, TRUE,
                    $6, $7, $8, $9, $10, $11, $12)
            RETURNING id::text
            """,
            tenant_key, org_id, report.task_id, report.job_id,
            version, report.overall_verdict,
            report.attachment_count, report.total_pages_analyzed,
            report.langfuse_trace_id,
            report.tokens_consumed, report.duration_seconds,
            markdown_report,
        )
        report_id = report_row["id"]

        # Insert criteria results
        if report.criteria_results:
            await conn.executemany(
                f"""
                INSERT INTO {_CRITERIA}
                    (report_id, criterion_id, criterion_text, verdict,
                     threshold_met, justification, gap_analysis,
                     evidence_references, conflicting_references,
                     agent_run_id, langfuse_trace_id)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7, $8, $9, $10::uuid, $11)
                """,
                [
                    (
                        report_id,
                        r.criterion_id,
                        r.criterion_text,
                        r.verdict,
                        r.threshold_met,
                        r.justification,
                        r.gap_analysis,
                        json.dumps([_ref_to_dict(ref) for ref in r.evidence_references]),
                        json.dumps([_ref_to_dict(ref) for ref in r.conflicting_references]),
                        r.agent_run_id,
                        r.langfuse_trace_id,
                    )
                    for r in report.criteria_results
                ],
            )

        return report_id

    # ── Report reads ─────────────────────────────────────────────────────────

    async def get_active_report(
        self,
        conn: asyncpg.Connection,
        *,
        task_id: str,
        tenant_key: str,
    ) -> dict | None:
        row = await conn.fetchrow(
            f"""
            SELECT r.id::text, r.tenant_key, r.org_id::text, r.task_id::text,
                   r.job_id::text, r.version, r.is_active, r.overall_verdict,
                   r.attachment_count, r.total_pages_analyzed,
                   r.langfuse_trace_id, r.tokens_consumed, r.duration_seconds,
                   r.created_at::text,
                   (r.markdown_report IS NOT NULL) AS markdown_report_available
            FROM {_REPORTS} r
            WHERE r.task_id = $1::uuid AND r.tenant_key = $2
              AND r.is_active = TRUE AND r.is_deleted = FALSE
            LIMIT 1
            """,
            task_id, tenant_key,
        )
        if not row:
            return None
        report = dict(row)

        # Fetch criteria results
        criteria_rows = await conn.fetch(
            f"""
            SELECT id::text, criterion_id::text, criterion_text, verdict,
                   threshold_met, justification, gap_analysis,
                   evidence_references, conflicting_references,
                   agent_run_id::text, langfuse_trace_id
            FROM {_CRITERIA}
            WHERE report_id = $1::uuid AND is_deleted = FALSE
            ORDER BY created_at
            """,
            report["id"],
        )
        report["criteria_results"] = []
        for cr in criteria_rows:
            d = dict(cr)
            for key in ("evidence_references", "conflicting_references"):
                if isinstance(d.get(key), str):
                    try:
                        d[key] = json.loads(d[key])
                    except Exception as _je:
                        _logger.warning("Failed to parse %s JSON for criterion %s: %s", key, d.get("id"), _je)
                        d[key] = []
            report["criteria_results"].append(d)

        return report

    async def list_reports(
        self,
        conn: asyncpg.Connection,
        *,
        task_id: str,
        tenant_key: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        rows = await conn.fetch(
            f"""
            SELECT id::text, version, overall_verdict, attachment_count,
                   total_pages_analyzed, created_at::text
            FROM {_REPORTS}
            WHERE task_id = $1::uuid AND tenant_key = $2 AND is_deleted = FALSE
            ORDER BY version DESC
            LIMIT $3 OFFSET $4
            """,
            task_id, tenant_key, limit, offset,
        )
        return [dict(r) for r in rows]

    async def get_report_by_id(
        self,
        conn: asyncpg.Connection,
        *,
        report_id: str,
        tenant_key: str,
    ) -> dict | None:
        row = await conn.fetchrow(
            f"""
            SELECT r.id::text, r.tenant_key, r.task_id::text, r.job_id::text,
                   r.version, r.is_active, r.overall_verdict,
                   r.attachment_count, r.total_pages_analyzed,
                   r.langfuse_trace_id, r.tokens_consumed,
                   r.duration_seconds, r.created_at::text,
                   (r.markdown_report IS NOT NULL) AS markdown_report_available
            FROM {_REPORTS} r
            WHERE r.id = $1::uuid AND r.tenant_key = $2 AND r.is_deleted = FALSE
            """,
            report_id, tenant_key,
        )
        if not row:
            return None
        report = dict(row)
        criteria_rows = await conn.fetch(
            f"""
            SELECT id::text, criterion_id::text, criterion_text, verdict,
                   threshold_met, justification, gap_analysis,
                   evidence_references, conflicting_references,
                   agent_run_id::text, langfuse_trace_id
            FROM {_CRITERIA}
            WHERE report_id = $1::uuid AND is_deleted = FALSE
            ORDER BY created_at
            """,
            report_id,
        )
        report["criteria_results"] = []
        for cr in criteria_rows:
            d = dict(cr)
            for key in ("evidence_references", "conflicting_references"):
                if isinstance(d.get(key), str):
                    try:
                        d[key] = json.loads(d[key])
                    except Exception as _je:
                        _logger.warning("Failed to parse %s JSON for criterion %s: %s", key, d.get("id"), _je)
                        d[key] = []
            report["criteria_results"].append(d)
        return report

    async def get_batch_verdicts(
        self,
        conn: asyncpg.Connection,
        *,
        task_ids: list[str],
        tenant_key: str,
    ) -> dict[str, str]:
        """
        Return {task_id: overall_verdict} for the active report of each task.
        Tasks with no active report are omitted from the result.
        Accepts up to 100 task IDs.
        """
        if not task_ids:
            return {}
        rows = await conn.fetch(
            f"""
            SELECT task_id::text, overall_verdict
            FROM {_REPORTS}
            WHERE task_id = ANY($1::uuid[])
              AND tenant_key = $2
              AND is_active = TRUE
              AND is_deleted = FALSE
            """,
            task_ids, tenant_key,
        )
        return {r["task_id"]: r["overall_verdict"] for r in rows}

    async def get_report_markdown(
        self,
        conn: asyncpg.Connection,
        *,
        report_id: str,
        tenant_key: str,
    ) -> str | None:
        """Lightweight fetch — returns only the markdown_report TEXT (or None)."""
        row = await conn.fetchrow(
            f"""
            SELECT markdown_report
            FROM {_REPORTS}
            WHERE id = $1::uuid AND tenant_key = $2 AND is_deleted = FALSE
            """,
            report_id, tenant_key,
        )
        if not row:
            return None
        return row["markdown_report"]

    # ── GDPR / soft delete ───────────────────────────────────────────────────

    async def anonymise_task_data(
        self,
        conn: asyncpg.Connection,
        *,
        task_id: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_JOBS}
            SET is_deleted = TRUE, attachment_ids = '[]', updated_at = NOW()
            WHERE task_id = $1::uuid
            """,
            task_id,
        )
        report_rows = await conn.fetch(
            f"SELECT id FROM {_REPORTS} WHERE task_id = $1::uuid",
            task_id,
        )
        for r in report_rows:
            await conn.execute(
                f"""
                UPDATE {_CRITERIA}
                SET is_deleted = TRUE,
                    evidence_references = '[]',
                    conflicting_references = '[]',
                    justification = '[redacted]',
                    criterion_text = '[redacted]'
                WHERE report_id = $1::uuid
                """,
                r["id"],
            )
        await conn.execute(
            f"UPDATE {_REPORTS} SET is_deleted = TRUE, markdown_report = NULL, updated_at = NOW() WHERE task_id = $1::uuid",
            task_id,
        )

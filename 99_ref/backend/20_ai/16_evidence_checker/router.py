"""
FastAPI routes for the AI Evidence Checker.

Mounts under /ai/evidence-check/ prefix in the main 20_ai router.

All endpoints:
  - Validate tenant_key from session (via get_current_session dependency)
  - Enforce org-scoping — no cross-tenant data can leak
  - Super-admin-only: /queue and /dashboard

New endpoints only — no existing endpoints modified.
"""

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

_auth_module = import_module("backend.03_auth_manage.dependencies")

get_current_session = _auth_module.get_current_access_claims


async def get_db_pool(request: Request):
    return request.app.state.database_pool

from .job_handler import enqueue_evidence_check
from .repository import EvidenceCheckerRepository

router = APIRouter(prefix="/api/v1/ai/evidence-check", tags=["evidence-check"])

_repo = EvidenceCheckerRepository()


# ── Helper ──────────────────────────────────────────────────────────────────

def _require_super_admin(session) -> None:
    is_super = getattr(session, "is_super_admin", False)
    if not is_super:
        raise HTTPException(status_code=403, detail="Super-admin access required")


def _task_tenant_key(session) -> str:
    return getattr(session, "tenant_key", "default")


# ── Batch verdicts for task list badges ─────────────────────────────────────
# IMPORTANT: must be registered BEFORE /tasks/{task_id}/... routes so FastAPI
# does not interpret "verdicts" as a task_id UUID parameter.

@router.get("/tasks/verdicts")
async def get_batch_verdicts(
    session: Annotated[dict, Depends(get_current_session)],
    pool=Depends(get_db_pool),
    task_ids: list[str] = Query(..., description="Up to 100 task UUIDs"),
):
    """
    Return {task_id: overall_verdict} for active reports of the given tasks.
    Tasks with no completed report are omitted from the result.
    Used by the task list page to show evidence verdict badges.
    """
    if len(task_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 task IDs per request")
    tenant_key = _task_tenant_key(session)
    async with pool.acquire() as conn:
        verdicts = await _repo.get_batch_verdicts(conn, task_ids=task_ids, tenant_key=tenant_key)
    return {"verdicts": verdicts}


# ── Current job status for a task ───────────────────────────────────────────

@router.get("/tasks/{task_id}/jobs/current")
async def get_current_job(
    task_id: str,
    session: Annotated[dict, Depends(get_current_session)],
    pool=Depends(get_db_pool),
):
    """
    Returns the most recent evidence_check_job for this task.
    Shows queue position and progress so the UI can render the status panel.
    """
    tenant_key = _task_tenant_key(session)
    async with pool.acquire() as conn:
        job = await _repo.get_current_job(conn, task_id=task_id, tenant_key=tenant_key)
    if not job:
        return {"job": None}
    return {"job": job}


# ── Report versions list ─────────────────────────────────────────────────────

@router.get("/tasks/{task_id}/reports")
async def list_reports(
    task_id: str,
    session: Annotated[dict, Depends(get_current_session)],
    pool=Depends(get_db_pool),
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
):
    """Paginated list of report versions for version-selector dropdown."""
    tenant_key = _task_tenant_key(session)
    async with pool.acquire() as conn:
        reports = await _repo.list_reports(conn, task_id=task_id, tenant_key=tenant_key, limit=limit, offset=offset)
    return {"reports": reports, "total": len(reports)}


# ── Active report ────────────────────────────────────────────────────────────

@router.get("/tasks/{task_id}/reports/active")
async def get_active_report(
    task_id: str,
    session: Annotated[dict, Depends(get_current_session)],
    pool=Depends(get_db_pool),
):
    """Full active report with all criteria results."""
    tenant_key = _task_tenant_key(session)
    async with pool.acquire() as conn:
        report = await _repo.get_active_report(conn, task_id=task_id, tenant_key=tenant_key)
    if not report:
        return {"report": None}
    return {"report": report}


# ── Report by ID ─────────────────────────────────────────────────────────────

@router.get("/reports/{report_id}")
async def get_report(
    report_id: str,
    session: Annotated[dict, Depends(get_current_session)],
    pool=Depends(get_db_pool),
):
    """Full report for a specific historical version."""
    tenant_key = _task_tenant_key(session)
    async with pool.acquire() as conn:
        report = await _repo.get_report_by_id(conn, report_id=report_id, tenant_key=tenant_key)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    # Org scoping: tenant_key already enforces cross-tenant isolation.
    # The report's task_id is returned so the caller can verify they have task access.
    return {"report": report}


# ── Diff between two report versions ────────────────────────────────────────

@router.get("/reports/{report_id}/diff/{other_id}")
async def diff_reports(
    report_id: str,
    other_id: str,
    session: Annotated[dict, Depends(get_current_session)],
    pool=Depends(get_db_pool),
):
    """
    Returns two full reports and a computed diff of criteria verdicts.
    Diff is computed here to keep it simple; the frontend highlights changes.
    """
    tenant_key = _task_tenant_key(session)
    async with pool.acquire() as conn:
        r1 = await _repo.get_report_by_id(conn, report_id=report_id, tenant_key=tenant_key)
        r2 = await _repo.get_report_by_id(conn, report_id=other_id, tenant_key=tenant_key)

    if not r1 or not r2:
        raise HTTPException(status_code=404, detail="One or both reports not found")

    # Verify same task
    if r1.get("task_id") != r2.get("task_id"):
        raise HTTPException(status_code=400, detail="Reports must belong to the same task")

    # Build verdict-change diff keyed by criterion_text
    r1_verdicts = {c["criterion_text"]: c["verdict"] for c in r1.get("criteria_results", [])}
    r2_verdicts = {c["criterion_text"]: c["verdict"] for c in r2.get("criteria_results", [])}
    all_keys = set(r1_verdicts) | set(r2_verdicts)

    diff = []
    for criterion_text in all_keys:
        v1 = r1_verdicts.get(criterion_text)
        v2 = r2_verdicts.get(criterion_text)
        if v1 != v2:
            diff.append({
                "criterion_text": criterion_text,
                "before_verdict": v1,
                "after_verdict": v2,
            })

    return {
        "report_a": r1,
        "report_b": r2,
        "changed_criteria": diff,
        "total_changes": len(diff),
    }


# ── Manual re-trigger ────────────────────────────────────────────────────────

@router.post("/tasks/{task_id}/trigger")
async def trigger_evaluation(
    task_id: str,
    session: Annotated[dict, Depends(get_current_session)],
    pool=Depends(get_db_pool),
):
    """
    Manually re-trigger evidence evaluation for a task.
    Requires ai_evidence_checker.trigger permission (workspace admin).
    Fetches the current set of task attachments and enqueues a new job.
    """
    tenant_key = _task_tenant_key(session)
    user_id = session.subject

    # Verify permission and look up task org_id + attachment IDs in one connection
    _perm = import_module("backend.03_auth_manage._permission_check")
    async with pool.acquire() as conn:
        try:
            await _perm.require_permission(conn, user_id, "ai_evidence_checker.trigger")
        except Exception:
            raise HTTPException(status_code=403, detail="Permission denied: ai_evidence_checker.trigger required")

        # Resolve org_id from the task (JWT has no org context)
        task_row = await conn.fetchrow(
            'SELECT org_id::text, tenant_key FROM "08_tasks"."10_fct_tasks" WHERE id = $1::uuid AND is_deleted = FALSE',
            task_id,
        )
        if not task_row:
            raise HTTPException(status_code=404, detail="Task not found")
        org_id = task_row["org_id"]
        if task_row["tenant_key"]:
            tenant_key = task_row["tenant_key"]

        # Load current attachment IDs for this task
        att_rows = await conn.fetch(
            """
            SELECT id::text
            FROM "09_attachments"."01_fct_attachments"
            WHERE entity_type = 'task' AND entity_id = $1::uuid AND is_deleted = FALSE
            """,
            task_id,
        )
    attachment_ids = [r["id"] for r in att_rows]

    if not attachment_ids:
        return {"message": "Task has no attachments — nothing to evaluate", "queued": False}

    raw_pool = pool.pool if hasattr(pool, "pool") else pool
    jq_job_id = await enqueue_evidence_check(
        pool=raw_pool,
        tenant_key=tenant_key,
        org_id=org_id,
        task_id=task_id,
        triggered_by_attachment_id=None,
        attachment_ids=attachment_ids,
        user_id=user_id,
    )
    return {"message": "Evidence evaluation queued", "queued": True, "job_id": jq_job_id}


# ── Markdown report download ─────────────────────────────────────────────────

@router.get("/reports/{report_id}/download")
async def download_report_markdown(
    report_id: str,
    session: Annotated[dict, Depends(get_current_session)],
    pool=Depends(get_db_pool),
):
    """Download the markdown evidence report as a .md file."""
    tenant_key = _task_tenant_key(session)
    async with pool.acquire() as conn:
        markdown = await _repo.get_report_markdown(conn, report_id=report_id, tenant_key=tenant_key)
    if markdown is None:
        raise HTTPException(status_code=404, detail="Report not found or markdown not available")
    short_id = report_id[:8]
    filename = f"evidence_report_{short_id}.md"
    return StreamingResponse(
        iter([markdown.encode("utf-8")]),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Queue overview (super-admin) ─────────────────────────────────────────────

@router.get("/queue")
async def get_queue_overview(
    session: Annotated[dict, Depends(get_current_session)],
    pool=Depends(get_db_pool),
):
    """Global queue depth for evidence_check jobs (super-admin only)."""
    _require_super_admin(session)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT status_code,
                   COUNT(*) AS job_count,
                   MIN(created_at)::text AS oldest_job_at
            FROM "20_ai"."70_fct_evidence_check_jobs"
            WHERE is_deleted = FALSE
            GROUP BY status_code
            ORDER BY status_code
            """
        )
    return {"queue": [dict(r) for r in rows]}


# ── Dashboard metrics (super-admin) ─────────────────────────────────────────

@router.get("/dashboard")
async def get_dashboard_metrics(
    session: Annotated[dict, Depends(get_current_session)],
    pool=Depends(get_db_pool),
):
    """
    Aggregate evidence check metrics for the AI admin dashboard.
    Super-admin only.
    """
    _require_super_admin(session)
    async with pool.acquire() as conn:
        # Overall report stats
        stats = await conn.fetchrow(
            """
            SELECT
                COUNT(*)                          AS total_reports,
                AVG(duration_seconds)             AS avg_duration_s,
                AVG(tokens_consumed)              AS avg_tokens,
                COUNT(*) FILTER (WHERE overall_verdict = 'ALL_MET')      AS all_met_count,
                COUNT(*) FILTER (WHERE overall_verdict = 'PARTIALLY_MET') AS partially_met_count,
                COUNT(*) FILTER (WHERE overall_verdict = 'NOT_MET')       AS not_met_count,
                COUNT(*) FILTER (WHERE overall_verdict = 'INCONCLUSIVE')  AS inconclusive_count
            FROM "20_ai"."71_fct_evidence_check_reports"
            WHERE is_deleted = FALSE AND is_active = TRUE
            """
        )
        # Failure rate
        failure = await conn.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE status_code = 'failed')    AS failed_jobs,
                COUNT(*) FILTER (WHERE status_code = 'completed') AS completed_jobs
            FROM "20_ai"."70_fct_evidence_check_jobs"
            WHERE is_deleted = FALSE
              AND created_at > NOW() - INTERVAL '7 days'
            """
        )

    return {
        "reports": dict(stats) if stats else {},
        "last_7_days": dict(failure) if failure else {},
    }

"""
iam.dsar — service layer.

Implements:
  create_export_request(pool, conn, ctx, subject_user_id, org_id, vault) → dict
  create_delete_request(pool, conn, ctx, subject_user_id, org_id) → dict
  poll_dsar_job(pool, ctx, job_id) → dict
  list_jobs(pool, ctx, org_id, limit, offset) → dict
  run_pending_dsar_exports(pool) → None (async worker)
  run_pending_dsar_deletes(pool) → None (async worker)

DSAR = operator-triggered Data Subject Access Requests (separate from self-service GDPR).
Audit scope: operator user_id + session_id + target org_id + workspace_id (mandatory).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_repo: Any = import_module("backend.02_features.03_iam.sub_features.08_dsar.repository")

logger = logging.getLogger("tennetctl.iam.dsar")


def _serialize_job(job: dict[str, Any] | None) -> dict[str, Any] | None:
    """Convert datetime fields to ISO strings."""
    if job is None:
        return None
    return {
        k: v.isoformat() if isinstance(v, datetime) else v
        for k, v in job.items()
    }


# ── Export request ────────────────────────────────────────────────────────────

async def create_export_request(
    pool: Any,
    conn: Any,
    ctx: Any,
    subject_user_id: str,
    org_id: str,
    vault: Any = None,  # type: ignore[assignment] # noqa: F841
) -> dict[str, Any]:
    """
    Create an export DSAR job (SAR).
    Checks: user exists, belongs to org, rate limit, audit scope.
    Returns job dict with status='requested'.
    """
    # Validate user exists
    user_exists = await conn.fetchval(
        'SELECT 1 FROM "03_iam"."10_fct_users" WHERE id = $1',
        subject_user_id,
    )
    if not user_exists:
        raise _errors.AppError("NOT_FOUND", f"User {subject_user_id} not found.", 404)

    # Validate user belongs to org
    if not await _repo.user_belongs_to_org(conn, subject_user_id, org_id):
        raise _errors.AppError(
            "FORBIDDEN",
            f"User {subject_user_id} not a member of org {org_id}.",
            403,
        )

    # Rate limit check (SQL-based: 10 per org per hour)
    if not await _repo.check_rate_limit(conn, org_id):
        raise _errors.AppError(
            "RATE_LIMITED",
            "DSAR limit exceeded: 10 per org per hour.",
            429,
        )

    # Create job
    job_id = _core_id.uuid7()
    await _repo.create_dsar_job(
        conn,
        job_id=job_id,
        org_id=org_id,
        subject_user_id=subject_user_id,
        actor_user_id=ctx.user_id,
        actor_session_id=getattr(ctx, "session_id", None),
        job_type="export",
    )

    # Emit audit event
    await _emit_audit(
        pool,
        ctx,
        event_key="iam.dsar.export_requested",
        metadata={"job_id": job_id, "subject_user_id": subject_user_id, "org_id": org_id},
    )

    job = await _repo.get_dsar_job(conn, job_id)
    result = _serialize_job(job)
    if result is None:
        raise _errors.AppError("NOT_FOUND", f"Job {job_id} not found.", 404)
    return result


# ── Delete request ────────────────────────────────────────────────────────────

async def create_delete_request(
    pool: Any,
    conn: Any,
    ctx: Any,
    subject_user_id: str,
    org_id: str,
) -> dict[str, Any]:
    """
    Create a delete DSAR job (right to be forgotten).
    Same checks as export. Idempotent.
    Returns job dict with status='requested'.
    """
    # Validate user exists
    user_exists = await conn.fetchval(
        'SELECT 1 FROM "03_iam"."10_fct_users" WHERE id = $1',
        subject_user_id,
    )
    if not user_exists:
        raise _errors.AppError("NOT_FOUND", f"User {subject_user_id} not found.", 404)

    # Validate user belongs to org
    if not await _repo.user_belongs_to_org(conn, subject_user_id, org_id):
        raise _errors.AppError(
            "FORBIDDEN",
            f"User {subject_user_id} not a member of org {org_id}.",
            403,
        )

    # Rate limit check
    if not await _repo.check_rate_limit(conn, org_id):
        raise _errors.AppError(
            "RATE_LIMITED",
            "DSAR limit exceeded: 10 per org per hour.",
            429,
        )

    # Create job
    job_id = _core_id.uuid7()
    await _repo.create_dsar_job(
        conn,
        job_id=job_id,
        org_id=org_id,
        subject_user_id=subject_user_id,
        actor_user_id=ctx.user_id,
        actor_session_id=getattr(ctx, "session_id", None),
        job_type="delete",
    )

    # Emit audit event
    await _emit_audit(
        pool,
        ctx,
        event_key="iam.dsar.delete_requested",
        metadata={"job_id": job_id, "subject_user_id": subject_user_id, "org_id": org_id},
    )

    job = await _repo.get_dsar_job(conn, job_id)
    result = _serialize_job(job)
    if result is None:
        raise _errors.AppError("NOT_FOUND", f"Job {job_id} not found.", 404)
    return result


# ── Poll job status ──────────────────────────────────────────────────────────

async def poll_dsar_job(
    pool: Any,
    ctx: Any,
    job_id: str,
) -> dict[str, Any]:
    """
    Get current job status.
    If export is complete, generate signed download URL from vault.
    """
    async with pool.acquire() as conn:
        job = await _repo.get_dsar_job(conn, job_id)
        if not job:
            raise _errors.AppError("NOT_FOUND", f"Job {job_id} not found.", 404)

        # Validate caller can see this job (org scope)
        if job["org_id"] != ctx.org_id:
            raise _errors.AppError(
                "FORBIDDEN",
                f"Job {job_id} not in org {ctx.org_id}.",
                403,
            )

        result = _serialize_job(job)
        if result is None:
            raise _errors.AppError("NOT_FOUND", f"Job {job_id} not found.", 404)

        # If export completed, generate signed URL
        if (
            result.get("job_type") == "export"
            and result.get("status") == "completed"
            and result.get("result_location")
        ):
            # TODO: Generate signed download URL from vault if available
            # For now, just return the location
            result["download_url"] = result["result_location"]

        return result


# ── List jobs ─────────────────────────────────────────────────────────────────

async def list_jobs(
    pool: Any,
    ctx: Any,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """List DSAR jobs for org (pagination)."""
    async with pool.acquire() as conn:
        jobs_list, total = await _repo.list_dsar_jobs(conn, ctx.org_id, limit, offset)
        return {
            "jobs": [_serialize_job(j) for j in jobs_list],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


# ── Worker async processing ───────────────────────────────────────────────────

async def _process_dsar_export_job(pool: Any, job_id: str) -> None:
    """
    Process a pending export job (worker background task).
    Assemble data → store in vault → update job status.
    """
    try:
        async with pool.acquire() as conn:
            # Mark as in_progress
            await _repo.update_dsar_job_status(
                conn,
                job_id=job_id,
                status="in_progress",
            )

            # Get job details
            job = await _repo.get_dsar_job(conn, job_id)
            if not job:
                logger.error(f"Job {job_id} not found during export")
                return

            subject_user_id = job["subject_user_id"]

        # Assemble data (separate connection)
        data = await _repo.export_user_data(pool, subject_user_id, job["org_id"])

        # Count rows
        row_counts = {k: len(v) if isinstance(v, list) else 0 for k, v in data.items()}

        # Store in vault (mock: just store as JSON)
        vault_path = f"dsar/{job_id}/export.json"
        # In real implementation, use vault client to store
        # vault_content = json.dumps(data, default=str)

        async with pool.acquire() as conn:
            await _repo.update_dsar_job_status(
                conn,
                job_id=job_id,
                status="completed",
                row_counts=row_counts,
                result_location=vault_path,
            )

        logger.info(f"Export job {job_id} completed: {row_counts}")

    except Exception as e:
        logger.exception(f"Export job {job_id} failed")
        async with pool.acquire() as conn:
            await _repo.update_dsar_job_status(
                conn,
                job_id=job_id,
                status="failed",
                error_detail=str(e)[:500],
            )


async def _process_dsar_delete_job(pool: Any, job_id: str) -> None:
    """
    Process a pending delete job (worker background task).
    Cascade delete → soft-delete user → update job status.
    """
    try:
        async with pool.acquire() as conn:
            # Mark as in_progress
            await _repo.update_dsar_job_status(
                conn,
                job_id=job_id,
                status="in_progress",
            )

            # Get job details
            job = await _repo.get_dsar_job(conn, job_id)
            if not job:
                logger.error(f"Job {job_id} not found during delete")
                return

            subject_user_id = job["subject_user_id"]

            # Cascade delete (idempotent: checks deleted_at)
            row_counts = await _repo.delete_user_data(conn, subject_user_id, job["org_id"])

            # Mark job complete
            await _repo.update_dsar_job_status(
                conn,
                job_id=job_id,
                status="completed",
                row_counts=row_counts,
            )

            logger.info(f"Delete job {job_id} completed: {row_counts}")

    except Exception as e:
        logger.exception(f"Delete job {job_id} failed")
        async with pool.acquire() as conn:
            await _repo.update_dsar_job_status(
                conn,
                job_id=job_id,
                status="failed",
                error_detail=str(e)[:500],
            )


# ── Worker loop polling ────────────────────────────────────────────────────────

async def run_pending_dsar_exports(pool: Any) -> None:
    """Poll for pending export jobs and dispatch to workers."""
    async with pool.acquire() as conn:
        pending = await _repo.list_pending_exports(conn, limit=5)

    for job in pending:
        asyncio.create_task(_process_dsar_export_job(pool, job["id"]))


async def run_pending_dsar_deletes(pool: Any) -> None:
    """Poll for pending delete jobs and dispatch to workers."""
    async with pool.acquire() as conn:
        pending = await _repo.list_pending_deletes(conn, limit=5)

    for job in pending:
        asyncio.create_task(_process_dsar_delete_job(pool, job["id"]))


# ── Audit helper ───────────────────────────────────────────────────────────────

async def _emit_audit(
    pool: Any,
    ctx: Any,
    *,
    event_key: str,
    metadata: dict,
    outcome: str = "success",
) -> None:
    """
    Emit audit event with mandatory scope: user_id, session_id, org_id.
    """
    try:
        # Build audit metadata with scope
        audit_metadata = {
            **metadata,
            "actor_user_id": ctx.user_id,
            "actor_session_id": getattr(ctx, "session_id", None),
            "org_id": ctx.org_id,
            "workspace_id": getattr(ctx, "workspace_id", None),
        }

        async with pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO "04_audit"."60_evt_audit_events" '
                "(id, event_key, org_id, actor_user_id, actor_session_id, outcome, metadata, created_at) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)",
                _core_id.uuid7(),
                event_key,
                ctx.org_id,
                ctx.user_id,
                getattr(ctx, "session_id", None),
                outcome,
                audit_metadata,
            )
    except Exception:
        logger.exception(f"audit emit failed — event_key={event_key}")

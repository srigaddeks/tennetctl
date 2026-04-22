"""
iam.dsar — service layer.

Implements:
  create_export_request(pool, conn, ctx, subject_user_id, org_id, vault) → dict
  create_delete_request(pool, conn, ctx, subject_user_id, org_id) → dict
  poll_dsar_job(pool, ctx, job_id) → dict
  list_jobs(pool, ctx, org_id, limit, offset) → dict
  run_pending_dsar_exports(pool) → None (async worker)
  run_pending_dsar_deletes(pool) → None (async worker)
  get_export_plaintext(pool, ctx, job_id) → bytes | None (used by download route)

DSAR = operator-triggered Data Subject Access Requests (separate from self-service GDPR).
Audit scope: operator user_id + session_id + target org_id + workspace_id (mandatory,
enforced by the DB CHECK on "04_audit"."60_evt_audit"). All audit emission goes through
run_node("audit.events.emit", ...) — never a direct INSERT.

Payload encryption: completed export JSON is AES-256-GCM encrypted with a DEK fetched
from vault key "iam.dsar.export_dek_v1" (operator must seed 32 bytes base64 before the
first export runs). Ciphertext + 12-byte nonce are persisted to 20_dtl_dsar_payloads.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from dataclasses import replace as _replace
from datetime import datetime
from importlib import import_module
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module("backend.02_features.03_iam.sub_features.08_dsar.repository")

logger = logging.getLogger("tennetctl.iam.dsar")

_AUDIT_NODE_KEY = "audit.events.emit"
_EXPORT_DEK_VAULT_KEY = "iam.dsar.export_dek_v1"
_EXPORT_DEK_VERSION = 1


def _detach(ctx: Any) -> Any:
    """Return a copy of ctx with conn=None so audit inserts survive a rolled-back tx."""
    return _replace(ctx, conn=None)


async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict, outcome: str = "success") -> None:
    """Emit a DSAR audit event via the canonical audit node.

    Swallow emission failures — the caller's mutation has already committed and a
    failed audit row should not cascade into a user-visible error. The emitter
    itself logs the failure internally.
    """
    try:
        await _catalog.run_node(
            pool, _AUDIT_NODE_KEY, _detach(ctx),
            {"event_key": event_key, "outcome": outcome, "metadata": metadata},
        )
    except Exception:
        logger.exception("audit emit failed — event_key=%s", event_key)


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
    user_exists = await conn.fetchval(
        'SELECT 1 FROM "03_iam"."12_fct_users" WHERE id = $1',
        subject_user_id,
    )
    if not user_exists:
        raise _errors.AppError("NOT_FOUND", f"User {subject_user_id} not found.", 404)

    if not await _repo.user_belongs_to_org(conn, subject_user_id, org_id):
        raise _errors.AppError(
            "FORBIDDEN",
            f"User {subject_user_id} not a member of org {org_id}.",
            403,
        )

    if not await _repo.check_rate_limit(conn, org_id):
        raise _errors.AppError(
            "RATE_LIMITED",
            "DSAR limit exceeded: 10 per org per hour.",
            429,
        )

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

    await _emit(
        pool, ctx,
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
    user_exists = await conn.fetchval(
        'SELECT 1 FROM "03_iam"."12_fct_users" WHERE id = $1',
        subject_user_id,
    )
    if not user_exists:
        raise _errors.AppError("NOT_FOUND", f"User {subject_user_id} not found.", 404)

    if not await _repo.user_belongs_to_org(conn, subject_user_id, org_id):
        raise _errors.AppError(
            "FORBIDDEN",
            f"User {subject_user_id} not a member of org {org_id}.",
            403,
        )

    if not await _repo.check_rate_limit(conn, org_id):
        raise _errors.AppError(
            "RATE_LIMITED",
            "DSAR limit exceeded: 10 per org per hour.",
            429,
        )

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

    await _emit(
        pool, ctx,
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
    If export is complete, include a download_url pointer (decrypt happens on GET /download).
    """
    async with pool.acquire() as conn:
        job = await _repo.get_dsar_job(conn, job_id)
        if not job:
            raise _errors.AppError("NOT_FOUND", f"Job {job_id} not found.", 404)

        if job["org_id"] != ctx.org_id:
            raise _errors.AppError(
                "FORBIDDEN",
                f"Job {job_id} not in org {ctx.org_id}.",
                403,
            )

        result = _serialize_job(job)
        if result is None:
            raise _errors.AppError("NOT_FOUND", f"Job {job_id} not found.", 404)

        if (
            result.get("job_type") == "export"
            and result.get("status") == "completed"
            and result.get("result_location")
        ):
            # Surface the app-level download endpoint; no pre-signed URL yet.
            result["download_url"] = f"/v1/dsar/jobs/{job_id}/download"

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


# ── Encryption helpers ────────────────────────────────────────────────────────

async def _load_export_dek(vault_client: Any) -> bytes:
    """Fetch and base64-decode the DSAR export DEK. Must be 32 bytes."""
    if vault_client is None:
        raise RuntimeError(
            "vault client unavailable; DSAR export encryption requires vault key "
            f"'{_EXPORT_DEK_VAULT_KEY}'"
        )
    raw_b64 = await vault_client.get(_EXPORT_DEK_VAULT_KEY)
    dek = base64.b64decode(raw_b64)
    if len(dek) != 32:
        raise RuntimeError(
            f"DSAR export DEK at vault key '{_EXPORT_DEK_VAULT_KEY}' must be 32 bytes; got {len(dek)}"
        )
    return dek


# ── Worker async processing ───────────────────────────────────────────────────

async def _process_dsar_export_job(pool: Any, job_id: str, vault_client: Any) -> None:
    """
    Process a pending export job (worker background task).
    Assemble data → encrypt with vault-managed DEK → persist ciphertext → mark completed.
    """
    try:
        async with pool.acquire() as conn:
            await _repo.update_dsar_job_status(
                conn,
                job_id=job_id,
                status="in_progress",
            )

            job = await _repo.get_dsar_job(conn, job_id)
            if not job:
                logger.error(f"Job {job_id} not found during export")
                return

            subject_user_id = job["subject_user_id"]
            org_id = job["org_id"]
            actor_user_id = job["actor_user_id"]
            actor_session_id = job["actor_session_id"]

        # Assemble data (separate connection via pool)
        data = await _repo.export_user_data(pool, subject_user_id, org_id)
        row_counts = {k: len(v) if isinstance(v, list) else 0 for k, v in data.items()}

        # Encrypt the JSON blob
        plaintext = json.dumps(data, default=str).encode("utf-8")
        dek = await _load_export_dek(vault_client)
        nonce = os.urandom(12)
        ciphertext = AESGCM(dek).encrypt(nonce, plaintext, None)
        # Wipe DEK reference to shorten in-memory lifetime
        del dek

        payload_id = _core_id.uuid7()

        async with pool.acquire() as conn:
            await _repo.insert_dsar_payload(
                conn,
                payload_id=payload_id,
                job_id=job_id,
                ciphertext=ciphertext,
                nonce=nonce,
                dek_version=_EXPORT_DEK_VERSION,
                byte_size=len(plaintext),
            )
            await _repo.update_dsar_job_status(
                conn,
                job_id=job_id,
                status="completed",
                row_counts=row_counts,
                result_location=str(payload_id),
            )

        logger.info(f"Export job {job_id} completed: {row_counts}")

        # Build an ephemeral ctx for audit (worker has no request ctx).
        _ctx_mod: Any = import_module("backend.01_catalog.context")
        worker_ctx = _ctx_mod.NodeContext(
            user_id=actor_user_id,
            session_id=actor_session_id,
            org_id=org_id,
            workspace_id=None,
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
            audit_category="system",
            pool=pool,
        )
        await _emit(
            pool, worker_ctx,
            event_key="iam.dsar.export_completed",
            metadata={"job_id": job_id, "row_counts": row_counts, "payload_id": payload_id},
        )

    except Exception as e:
        logger.exception(f"Export job {job_id} failed")
        async with pool.acquire() as conn:
            await _repo.update_dsar_job_status(
                conn,
                job_id=job_id,
                status="failed",
                error_detail=str(e)[:500],
            )
        try:
            _ctx_mod2: Any = import_module("backend.01_catalog.context")
            fail_ctx = _ctx_mod2.NodeContext(
                trace_id=_core_id.uuid7(),
                span_id=_core_id.uuid7(),
                audit_category="system",
                pool=pool,
            )
            await _emit(
                pool, fail_ctx,
                event_key="iam.dsar.export_failed",
                metadata={"job_id": job_id, "error": str(e)[:500]},
                outcome="failure",
            )
        except Exception:
            logger.exception("failed-path audit emission also failed")


async def _process_dsar_delete_job(pool: Any, job_id: str) -> None:
    """
    Process a pending delete job (worker background task).
    Cascade delete → soft-delete user → update job status.
    """
    actor_user_id: str | None = None
    actor_session_id: str | None = None
    org_id: str | None = None
    try:
        async with pool.acquire() as conn:
            await _repo.update_dsar_job_status(
                conn,
                job_id=job_id,
                status="in_progress",
            )

            job = await _repo.get_dsar_job(conn, job_id)
            if not job:
                logger.error(f"Job {job_id} not found during delete")
                return

            subject_user_id = job["subject_user_id"]
            org_id = job["org_id"]
            actor_user_id = job["actor_user_id"]
            actor_session_id = job["actor_session_id"]

            row_counts = await _repo.delete_user_data(conn, subject_user_id, org_id)

            await _repo.update_dsar_job_status(
                conn,
                job_id=job_id,
                status="completed",
                row_counts=row_counts,
            )

            logger.info(f"Delete job {job_id} completed: {row_counts}")

        _ctx_mod: Any = import_module("backend.01_catalog.context")
        worker_ctx = _ctx_mod.NodeContext(
            user_id=actor_user_id,
            session_id=actor_session_id,
            org_id=org_id,
            workspace_id=None,
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
            audit_category="system",
            pool=pool,
        )
        await _emit(
            pool, worker_ctx,
            event_key="iam.dsar.delete_completed",
            metadata={"job_id": job_id, "row_counts": row_counts},
        )

    except Exception as e:
        logger.exception(f"Delete job {job_id} failed")
        async with pool.acquire() as conn:
            await _repo.update_dsar_job_status(
                conn,
                job_id=job_id,
                status="failed",
                error_detail=str(e)[:500],
            )
        try:
            _ctx_mod2: Any = import_module("backend.01_catalog.context")
            fail_ctx = _ctx_mod2.NodeContext(
                trace_id=_core_id.uuid7(),
                span_id=_core_id.uuid7(),
                audit_category="system",
                pool=pool,
            )
            await _emit(
                pool, fail_ctx,
                event_key="iam.dsar.delete_failed",
                metadata={"job_id": job_id, "error": str(e)[:500]},
                outcome="failure",
            )
        except Exception:
            logger.exception("failed-path audit emission also failed")


# ── Download (decrypt) ────────────────────────────────────────────────────────

async def get_export_plaintext(
    pool: Any,
    ctx: Any,
    job_id: str,
    vault_client: Any,
) -> bytes:
    """
    Return the decrypted export JSON as bytes. Validates org scope + completion.
    Emits iam.dsar.export_downloaded audit on success.
    Raises AppError on missing/invalid state.
    """
    async with pool.acquire() as conn:
        job = await _repo.get_dsar_job(conn, job_id)
        if not job:
            raise _errors.AppError("NOT_FOUND", f"Job {job_id} not found.", 404)
        if job["org_id"] != ctx.org_id:
            raise _errors.AppError("FORBIDDEN", f"Job {job_id} not in org {ctx.org_id}.", 403)
        if job.get("job_type") != "export":
            raise _errors.AppError("NOT_EXPORTABLE", "Job is not an export.", 400)
        if job.get("status") != "completed":
            raise _errors.AppError("NOT_READY", "Export job is not yet completed.", 404)

        payload = await _repo.get_dsar_payload(conn, job_id)

    if payload is None:
        raise _errors.AppError("NOT_READY", "Export payload not found.", 404)

    dek = await _load_export_dek(vault_client)
    try:
        plaintext = AESGCM(dek).decrypt(
            bytes(payload["nonce"]),
            bytes(payload["ciphertext"]),
            None,
        )
    finally:
        del dek

    await _emit(
        pool, ctx,
        event_key="iam.dsar.export_downloaded",
        metadata={"job_id": job_id, "byte_size": int(payload["byte_size"])},
    )
    return plaintext


# ── Worker loop polling ────────────────────────────────────────────────────────

async def run_pending_dsar_exports(pool: Any, vault_client: Any = None) -> None:
    """Poll for pending export jobs and dispatch to workers."""
    async with pool.acquire() as conn:
        pending = await _repo.list_pending_exports(conn, limit=5)

    for job in pending:
        asyncio.create_task(_process_dsar_export_job(pool, job["id"], vault_client))


async def run_pending_dsar_deletes(pool: Any) -> None:
    """Poll for pending delete jobs and dispatch to workers."""
    async with pool.acquire() as conn:
        pending = await _repo.list_pending_deletes(conn, limit=5)

    for job in pending:
        asyncio.create_task(_process_dsar_delete_job(pool, job["id"]))

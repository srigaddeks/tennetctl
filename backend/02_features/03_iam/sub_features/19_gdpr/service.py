"""
iam.gdpr — service layer.

Implements:
  request_export(pool, conn, ctx, user_id, vault_client) → GdprJob dict
  request_erasure(pool, conn, ctx, user_id, vault_client, password, totp_code=None) → GdprJob dict
  assemble_bundle(pool, user_id) → dict   (called from worker)
  run_pending_exports(pool)               (worker loop)
  run_pending_erasures(pool)              (worker loop)

Erasure pseudonymizes immediately; hard purge of evt_audit PII after hard_erase_at.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime, timedelta
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.19_gdpr.repository"
)
_users_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.repository"
)
_cred_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.08_credentials.service"
)

logger = logging.getLogger("tennetctl.iam.gdpr")

_AUDIT_NODE_KEY = "audit.events.emit"
_NOTIFY_NODE_KEY = "notify.send.transactional"

_GDPR_EXPORT_DIR = os.environ.get("GDPR_EXPORT_DIR", "/tmp/tennetctl_gdpr_exports")
_ERASE_RECOVERY_DAYS = 30


# ── helpers ───────────────────────────────────────────────────────────────────

async def _emit_audit(
    pool: Any, ctx: Any, *, event_key: str, metadata: dict, outcome: str = "success"
) -> None:
    from dataclasses import replace as _replace
    try:
        emit_ctx = _replace(ctx, conn=None) if outcome == "failure" else ctx
        await _catalog.run_node(
            pool, _AUDIT_NODE_KEY, emit_ctx,
            {"event_key": event_key, "outcome": outcome, "metadata": metadata},
        )
    except Exception:
        logger.exception("audit emit failed — event_key=%s", event_key)


# ── export ────────────────────────────────────────────────────────────────────

async def request_export(
    pool: Any, conn: Any, ctx: Any, user_id: str, vault_client: Any
) -> dict:
    """Create a queued export job. Worker picks it up asynchronously."""
    job_id = _core_id.uuid7()
    await _repo.insert_job(
        conn,
        id=job_id,
        user_id=user_id,
        kind_code="export",
        status_code="queued",
        created_by=user_id,
    )
    await _emit_audit(
        pool, ctx,
        event_key="iam.gdpr.export_requested",
        metadata={"job_id": job_id},
    )
    return await _repo.get_job(conn, job_id)


async def assemble_bundle(pool: Any, user_id: str) -> dict:
    """Assemble a JSON bundle of all data we hold for the user."""
    async with pool.acquire() as conn:
        user = await _users_repo.get_by_id(conn, user_id)
        if user is None:
            # Pseudonymized user — return minimal info
            user = {"id": user_id, "note": "account deleted / pseudonymized"}

        # Sessions
        sessions = await conn.fetch(
            'SELECT id, org_id, workspace_id, created_at, expires_at, revoked_at '
            'FROM "03_iam"."16_fct_sessions" WHERE user_id = $1',
            user_id,
        )

        # Org memberships
        memberships = await conn.fetch(
            'SELECT org_id, workspace_id, created_at '
            'FROM "03_iam"."40_lnk_org_members" WHERE user_id = $1 AND deleted_at IS NULL',
            user_id,
        )

        # Audit events where actor = user
        audit_events = await conn.fetch(
            'SELECT id, event_key, outcome, created_at '
            'FROM "04_audit"."60_evt_audit" WHERE actor_id = $1 '
            'ORDER BY created_at DESC LIMIT 1000',
            user_id,
        )

    def _ser(v: Any) -> Any:
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    def _row(r: Any) -> dict:
        return {k: _ser(v) for k, v in dict(r).items()}

    return {
        "exported_at": datetime.utcnow().isoformat(),
        "user": _row(user) if isinstance(user, dict) else user,
        "sessions": [_row(r) for r in sessions],
        "memberships": [_row(r) for r in memberships],
        "audit_events": [_row(r) for r in audit_events],
    }


async def _write_bundle_local(bundle: dict, job_id: str) -> str:
    """Write bundle to local fs. Returns path."""
    os.makedirs(_GDPR_EXPORT_DIR, exist_ok=True)
    path = os.path.join(_GDPR_EXPORT_DIR, f"{job_id}.json")
    with open(path, "w") as fh:
        json.dump(bundle, fh, indent=2)
    return path


async def _process_export_job(pool: Any, job_id: str, user_id: str) -> None:
    """Assemble + write bundle, update job status, send notify."""
    async with pool.acquire() as conn:
        await _repo.update_job_status(
            conn, job_id=job_id, status_code="processing", updated_by=user_id
        )
    try:
        bundle = await assemble_bundle(pool, user_id)
        path = await _write_bundle_local(bundle, job_id)
        # Hash the path as a simple token (not a signed URL for v0.1.6)
        url_hash = hashlib.sha256(path.encode()).hexdigest()[:32]
        async with pool.acquire() as conn:
            await _repo.update_job_status(
                conn,
                job_id=job_id,
                status_code="completed",
                download_url_hash=url_hash,
                updated_by=user_id,
            )
        logger.info("GDPR export complete job=%s path=%s", job_id, path)
    except Exception as exc:
        logger.exception("GDPR export failed job=%s", job_id)
        async with pool.acquire() as conn:
            await _repo.update_job_status(
                conn,
                job_id=job_id,
                status_code="failed",
                error_detail=str(exc),
                updated_by=user_id,
            )


# ── erasure ───────────────────────────────────────────────────────────────────

async def _pseudonymize_user(conn: Any, user_id: str) -> None:
    """
    Inline pseudonymization — replaces PII attrs and soft-deletes the user.
    Does NOT depend on 21-04's soft_delete_user.
    """
    _USER_ENTITY_TYPE_ID = 3
    pseudo_email = f"deleted-{user_id}@removed.local"
    pseudo_name = "[deleted user]"

    # Upsert email attr
    for attr_code, value in [("email", pseudo_email), ("display_name", pseudo_name)]:
        attr_def = await conn.fetchrow(
            'SELECT id FROM "03_iam"."20_dtl_attr_defs" '
            "WHERE entity_type_id = $1 AND code = $2",
            _USER_ENTITY_TYPE_ID, attr_code,
        )
        if attr_def:
            attr_def_id = attr_def["id"]
            await conn.execute(
                'UPDATE "03_iam"."21_dtl_attrs" '
                "SET key_text = $1, updated_at = CURRENT_TIMESTAMP "
                "WHERE entity_type_id = $2 AND entity_id = $3 AND attr_def_id = $4",
                value, _USER_ENTITY_TYPE_ID, user_id, attr_def_id,
            )

    # Soft-delete the fct_users row
    await conn.execute(
        'UPDATE "03_iam"."10_fct_users" '
        "SET deleted_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE id = $2 AND deleted_at IS NULL",
        user_id, user_id,
    )

    # Revoke all active sessions
    await conn.execute(
        'UPDATE "03_iam"."16_fct_sessions" '
        "SET revoked_at = CURRENT_TIMESTAMP, "
        "    updated_at = CURRENT_TIMESTAMP, "
        "    updated_by = $1 "
        "WHERE user_id = $2 AND revoked_at IS NULL AND deleted_at IS NULL",
        user_id, user_id,
    )


async def request_erasure(
    pool: Any,
    conn: Any,
    ctx: Any,
    user_id: str,
    vault_client: Any,
    password: str,
    totp_code: str | None = None,
) -> dict:
    """
    Verify identity, create erase job with 30-day recovery window,
    then immediately pseudonymize and revoke sessions.
    """
    # 1. Verify password
    ok = await _cred_service.verify_password(
        conn, vault_client=vault_client, user_id=user_id, value=password
    )
    if not ok:
        raise _errors.UnauthorizedError("Password is incorrect")

    # 2. TOTP check if provided — basic validation (full TOTP check is in 12_otp)
    if totp_code is not None:
        _otp_service: Any = import_module(
            "backend.02_features.03_iam.sub_features.12_otp.service"
        )
        totp_ok = await _otp_service.verify_totp(conn, user_id=user_id, code=totp_code)
        if not totp_ok:
            raise _errors.UnauthorizedError("TOTP code is incorrect")

    # 3. Insert erase job
    job_id = _core_id.uuid7()
    hard_erase_at = datetime.utcnow() + timedelta(days=_ERASE_RECOVERY_DAYS)
    await _repo.insert_job(
        conn,
        id=job_id,
        user_id=user_id,
        kind_code="erase",
        status_code="queued",
        hard_erase_at=hard_erase_at,
        created_by=user_id,
    )

    # 4. Pseudonymize immediately
    await _pseudonymize_user(conn, user_id)

    # 5. Audit (use setup category bypass — user+session just got revoked)
    from dataclasses import replace as _replace
    setup_ctx = _replace(ctx, audit_category="setup")
    await _emit_audit(
        pool, setup_ctx,
        event_key="iam.gdpr.erase_requested",
        metadata={"job_id": job_id, "hard_erase_at": hard_erase_at.isoformat()},
    )

    return await _repo.get_job(conn, job_id)


# ── hard purge ────────────────────────────────────────────────────────────────

async def _hard_purge_user_pii(pool: Any, user_id: str) -> None:
    """
    Nullify PII in evt_audit.metadata where actor = user.
    Preserves event rows — only removes identifying metadata fields.
    """
    async with pool.acquire() as conn:
        # Remove actor-identifying fields from audit metadata (preserve row structure)
        await conn.execute(
            'UPDATE "04_audit"."60_evt_audit" '
            "SET metadata = metadata - 'email' - 'display_name' - 'ip_address' "
            "WHERE actor_id = $1",
            user_id,
        )
        # Null out actor_id so event row is no longer linkable
        await conn.execute(
            'UPDATE "04_audit"."60_evt_audit" '
            "SET actor_id = NULL "
            "WHERE actor_id = $1",
            user_id,
        )
        logger.info("GDPR hard purge complete user=%s", user_id)


# ── worker loops ──────────────────────────────────────────────────────────────

async def run_pending_exports(pool: Any) -> None:
    """Pick up queued export jobs and process them."""
    async with pool.acquire() as conn:
        jobs = await _repo.list_queued_exports(conn)
    for job in jobs:
        await _process_export_job(pool, job["id"], job["user_id"])


async def run_pending_erasures(pool: Any) -> None:
    """Hard-purge PII for erase jobs where hard_erase_at has passed."""
    async with pool.acquire() as conn:
        jobs = await _repo.list_due_erasures(conn)
    for job in jobs:
        await _hard_purge_user_pii(pool, job["user_id"])
        async with pool.acquire() as conn:
            await _repo.update_job_status(
                conn,
                job_id=job["id"],
                status_code="completed",
                updated_by=job["user_id"],
            )
        logger.info("GDPR erasure job completed job=%s user=%s", job["id"], job["user_id"])


async def gdpr_worker_loop(pool: Any) -> None:
    """Background asyncio task — polls every 60 seconds."""
    while True:
        try:
            await run_pending_exports(pool)
        except Exception:
            logger.exception("GDPR export worker error")
        try:
            await run_pending_erasures(pool)
        except Exception:
            logger.exception("GDPR erasure worker error")
        await asyncio.sleep(60)

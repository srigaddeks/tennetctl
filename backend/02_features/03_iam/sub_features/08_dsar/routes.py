"""
iam.dsar — FastAPI routes.

Endpoints:
  POST   /v1/dsar/export-request    (202) — request SAR export
  POST   /v1/dsar/delete-request    (202) — request RTBF delete
  GET    /v1/dsar/jobs/{id}         (200) — poll job status
  GET    /v1/dsar/jobs              (200) — list org jobs with pagination
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Depends, Query

_resp: Any = import_module("backend.01_core.response")
_auth: Any = import_module("backend.01_core.auth")
_db: Any = import_module("backend.01_core.database")
_schemas: Any = import_module("backend.02_features.03_iam.sub_features.08_dsar.schemas")
_service: Any = import_module("backend.02_features.03_iam.sub_features.08_dsar.service")

router = APIRouter(prefix="/v1/dsar", tags=["iam.dsar"])


# ── Request SAR export ────────────────────────────────────────────────────────

@router.post("/export-request", status_code=202)
async def request_export(
    body: _schemas.DsarExportRequest,
    ctx: Any = Depends(_auth.get_context),  # type: ignore
    pool: Any = Depends(_db.get_pool),  # type: ignore
) -> dict[str, Any]:
    """
    Request a Subject Access Request (SAR) export.
    Operator-triggered. Returns job with status=requested.
    """
    async with pool.acquire() as conn:
        job = await _service.create_export_request(
            pool,
            conn,
            ctx,
            subject_user_id=body.subject_user_id,
            org_id=body.org_id,
        )
    return _resp.success_response(job)


# ── Request RTBF delete ───────────────────────────────────────────────────────

@router.post("/delete-request", status_code=202)
async def request_delete(
    body: _schemas.DsarDeleteRequest,
    ctx: Any = Depends(_auth.get_context),  # type: ignore
    pool: Any = Depends(_db.get_pool),  # type: ignore
) -> dict[str, Any]:
    """
    Request a right to be forgotten (RTBF) delete.
    Operator-triggered. Returns job with status=requested.
    """
    async with pool.acquire() as conn:
        job = await _service.create_delete_request(
            pool,
            conn,
            ctx,
            subject_user_id=body.subject_user_id,
            org_id=body.org_id,
        )
    return _resp.success_response(job)


# ── Poll job status ──────────────────────────────────────────────────────────

@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    ctx: Any = Depends(_auth.get_context),  # type: ignore
    pool: Any = Depends(_db.get_pool),  # type: ignore
) -> dict[str, Any]:
    """Poll a single DSAR job by ID."""
    job = await _service.poll_dsar_job(pool, ctx, job_id)
    return _resp.success_response(job)


# ── List org jobs ────────────────────────────────────────────────────────────

@router.get("/jobs")
async def list_jobs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    ctx: Any = Depends(_auth.get_context),  # type: ignore
    pool: Any = Depends(_db.get_pool),  # type: ignore
) -> dict[str, Any]:
    """List DSAR jobs for org with pagination."""
    result = await _service.list_jobs(pool, ctx, limit=limit, offset=offset)
    return _resp.success_list_response(
        result["jobs"],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )

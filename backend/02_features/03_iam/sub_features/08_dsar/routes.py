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

from fastapi import APIRouter, Query, Request

_resp: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_schemas: Any = import_module("backend.02_features.03_iam.sub_features.08_dsar.schemas")
_service: Any = import_module("backend.02_features.03_iam.sub_features.08_dsar.service")

router = APIRouter(prefix="/v1/dsar", tags=["iam.dsar"])


# ── Request SAR export ────────────────────────────────────────────────────────

@router.post("/export-request", status_code=202)
async def request_export(
    body: _schemas.DsarExportRequest,
    request: Request,
) -> Any:
    """
    Request a Subject Access Request (SAR) export.
    Operator-triggered. Returns job with status=requested.
    """
    user_id = getattr(request.state, "user_id", None)
    org_id_ctx = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)
    if not user_id or not org_id_ctx:
        raise _errors.UnauthorizedError("not signed in")

    class _Ctx:
        def __init__(self):
            self.user_id = user_id
            self.org_id = org_id_ctx
            self.session_id = session_id

    ctx = _Ctx()
    pool = request.app.state.pool
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
    request: Request,
) -> Any:
    """
    Request a right to be forgotten (RTBF) delete.
    Operator-triggered. Returns job with status=requested.
    """
    user_id = getattr(request.state, "user_id", None)
    org_id_ctx = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)
    if not user_id or not org_id_ctx:
        raise _errors.UnauthorizedError("not signed in")

    class _Ctx:
        def __init__(self):
            self.user_id = user_id
            self.org_id = org_id_ctx
            self.session_id = session_id

    ctx = _Ctx()
    pool = request.app.state.pool
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
    request: Request,
) -> Any:
    """Poll a single DSAR job by ID."""
    user_id = getattr(request.state, "user_id", None)
    org_id_ctx = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)
    if not user_id or not org_id_ctx:
        raise _errors.UnauthorizedError("not signed in")

    class _Ctx:
        def __init__(self):
            self.user_id = user_id
            self.org_id = org_id_ctx
            self.session_id = session_id

    ctx = _Ctx()
    pool = request.app.state.pool
    job = await _service.poll_dsar_job(pool, ctx, job_id)
    return _resp.success_response(job)


# ── List org jobs ────────────────────────────────────────────────────────────

@router.get("/jobs")
async def list_jobs(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> Any:
    """List DSAR jobs for org with pagination."""
    user_id = getattr(request.state, "user_id", None)
    org_id_ctx = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)
    if not user_id or not org_id_ctx:
        raise _errors.UnauthorizedError("not signed in")

    class _Ctx:
        def __init__(self):
            self.user_id = user_id
            self.org_id = org_id_ctx
            self.session_id = session_id

    ctx = _Ctx()
    pool = request.app.state.pool
    result = await _service.list_jobs(pool, ctx, limit=limit, offset=offset)
    return _resp.success_list_response(
        result["jobs"],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )

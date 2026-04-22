"""
iam.dsar — FastAPI routes.

Endpoints:
  POST   /v1/dsar/export-request        (202) — request SAR export
  POST   /v1/dsar/delete-request        (202) — request RTBF delete
  GET    /v1/dsar/jobs/{id}             (200) — poll job status
  GET    /v1/dsar/jobs                  (200) — list org jobs with pagination
  GET    /v1/dsar/jobs/{id}/download    (200) — stream decrypted export JSON
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

_resp: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_schemas: Any = import_module("backend.02_features.03_iam.sub_features.08_dsar.schemas")
_service: Any = import_module("backend.02_features.03_iam.sub_features.08_dsar.service")

DsarExportRequest = _schemas.DsarExportRequest
DsarDeleteRequest = _schemas.DsarDeleteRequest

router = APIRouter(prefix="/v1/dsar", tags=["iam.dsar"])


def _require_auth(request: Request) -> tuple[str, str, str | None]:
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)
    if not user_id or not org_id:
        raise _errors.UnauthorizedError("not signed in")
    return user_id, org_id, session_id


def _build_ctx(request: Request, pool: Any, user_id: str, org_id: str, session_id: str | None) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=user_id,
        session_id=session_id,
        org_id=org_id,
        workspace_id=getattr(request.state, "workspace_id", None),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="user",
        pool=pool,
        extras={"pool": pool},
    )


def _vault(request: Request) -> Any:
    return getattr(request.app.state, "vault", None)


# ── Request SAR export ────────────────────────────────────────────────────────

@router.post("/export-request", status_code=202)
async def request_export(
    body: DsarExportRequest,
    request: Request,
) -> Any:
    """
    Request a Subject Access Request (SAR) export.
    Operator-triggered. Returns job with status=requested.
    """
    user_id, org_id, session_id = _require_auth(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, user_id, org_id, session_id)
    async with pool.acquire() as conn:
        ctx_with_conn = ctx.__class__(**{**ctx.__dict__, "conn": conn}) if False else ctx
        # Replace conn on immutable dataclass via dataclasses.replace
        from dataclasses import replace as _replace
        ctx_with_conn = _replace(ctx, conn=conn)
        job = await _service.create_export_request(
            pool,
            conn,
            ctx_with_conn,
            subject_user_id=str(body.subject_user_id),
            org_id=str(body.org_id),
        )
    return _resp.success_response(job)


# ── Request RTBF delete ───────────────────────────────────────────────────────

@router.post("/delete-request", status_code=202)
async def request_delete(
    body: DsarDeleteRequest,
    request: Request,
) -> Any:
    """
    Request a right to be forgotten (RTBF) delete.
    Operator-triggered. Returns job with status=requested.
    """
    user_id, org_id, session_id = _require_auth(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, user_id, org_id, session_id)
    async with pool.acquire() as conn:
        from dataclasses import replace as _replace
        ctx_with_conn = _replace(ctx, conn=conn)
        job = await _service.create_delete_request(
            pool,
            conn,
            ctx_with_conn,
            subject_user_id=str(body.subject_user_id),
            org_id=str(body.org_id),
        )
    return _resp.success_response(job)


# ── Poll job status ──────────────────────────────────────────────────────────

@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    request: Request,
) -> Any:
    """Poll a single DSAR job by ID."""
    user_id, org_id, session_id = _require_auth(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, user_id, org_id, session_id)
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
    user_id, org_id, session_id = _require_auth(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, user_id, org_id, session_id)
    result = await _service.list_jobs(pool, ctx, limit=limit, offset=offset)
    return _resp.success_list_response(
        result["jobs"],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )


# ── Download (decrypt) export payload ─────────────────────────────────────────

@router.get("/jobs/{job_id}/download")
async def download_export(
    job_id: str,
    request: Request,
) -> Response:
    """
    Stream the decrypted DSAR export JSON.
    Requires vault access for the DEK. Emits iam.dsar.export_downloaded audit.
    """
    user_id, org_id, session_id = _require_auth(request)
    pool = request.app.state.pool
    vault = _vault(request)
    if vault is None:
        raise _errors.AppError(
            "VAULT_DISABLED",
            "vault module is not enabled; DSAR download requires vault access",
            status_code=503,
        )
    ctx = _build_ctx(request, pool, user_id, org_id, session_id)
    plaintext = await _service.get_export_plaintext(pool, ctx, job_id, vault)
    return Response(
        content=plaintext,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="dsar-{job_id}.json"',
            "Cache-Control": "no-store",
        },
    )

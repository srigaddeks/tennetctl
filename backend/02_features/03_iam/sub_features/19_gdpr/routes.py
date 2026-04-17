"""
iam.gdpr — FastAPI routes.

Routes:
  POST /v1/account/data-export   — request GDPR Art 15 export (auth required)
  POST /v1/account/delete-me     — request GDPR Art 17 erasure (auth required)
  GET  /v1/account/gdpr/status   — latest export + erase job for current user
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Depends, Request

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.19_gdpr.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.19_gdpr.service"
)
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.19_gdpr.repository"
)

EraseRequestIn = _schemas.EraseRequestIn

router = APIRouter(prefix="/v1/account", tags=["iam.gdpr"])


def _build_ctx(request: Request, pool: Any) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=getattr(request.state, "user_id", None),
        session_id=getattr(request.state, "session_id", None),
        org_id=getattr(request.state, "org_id", None),
        workspace_id=getattr(request.state, "workspace_id", None),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="iam",
        extras={"pool": pool},
    )


def _vault(request: Request) -> Any:
    v = getattr(request.app.state, "vault", None)
    if v is None:
        raise _errors.AppError("VAULT_DISABLED", "Vault not configured.", 503)
    return v


def _require_auth(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.UnauthorizedError("Authentication required")
    return user_id


@router.post("/data-export", status_code=202)
async def request_data_export(request: Request) -> Any:
    """Art 15 — request a data export. Job is processed asynchronously."""
    user_id = _require_auth(request)
    pool = request.app.state.pool
    vault = _vault(request)
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        job = await _service.request_export(pool, conn, ctx, user_id, vault)
    return _response.success_response(job)


@router.post("/delete-me", status_code=202)
async def request_erasure(request: Request, body: EraseRequestIn) -> Any:
    """Art 17 — request account erasure with 30-day recovery window."""
    user_id = _require_auth(request)
    pool = request.app.state.pool
    vault = _vault(request)
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        job = await _service.request_erasure(
            pool, conn, ctx, user_id, vault, body.password, body.totp_code
        )
    return _response.success_response(job)


@router.get("/gdpr/status")
async def gdpr_status(request: Request) -> Any:
    """Latest export + erase job for the current user."""
    user_id = _require_auth(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        export_job = await _repo.get_latest_by_user_kind(conn, user_id, "export")
        erase_job = await _repo.get_latest_by_user_kind(conn, user_id, "erase")
    return _response.success_response({"export": export_job, "erase": erase_job})

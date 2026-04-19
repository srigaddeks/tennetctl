"""HTTP routes for product_ops.referrals.

  GET    /v1/referrals                  — list codes (workspace-scoped)
  POST   /v1/referrals                  — admin create code
  GET    /v1/referrals/{id}             — get code
  DELETE /v1/referrals/{id}             — soft-delete code
  POST   /v1/referrals/attach           — anonymous attach (called from SDK landing handler)
  POST   /v1/referrals/conversions      — record a conversion (server-side from app)
"""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_schemas: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.03_referrals.schemas"
)
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.03_referrals.service"
)
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.03_referrals.repository"
)

logger = logging.getLogger("tennetctl.product_ops.referrals")
router = APIRouter(tags=["product_ops.referrals"])


def _build_anon_ctx(request: Request, pool: Any) -> Any:
    del request  # kept for symmetry with _build_session_ctx
    return _catalog_ctx.NodeContext(
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(),
        audit_category="setup",
        extras={"pool": pool},
    )


def _build_session_ctx(request: Request, pool: Any) -> Any:
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=getattr(state, "org_id", None) or request.headers.get("x-org-id"),
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", "") or _core_id.uuid7(),
        audit_category="user",
        extras={"pool": pool},
    )


def _enforce_ws(request: Request, workspace_id: str | None) -> str:
    state = request.state
    session_ws = getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id")
    if session_ws is None and workspace_id is None:
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "error": {"code": "BAD_REQUEST", "message": "workspace_id required"}},
        )
    if session_ws and workspace_id and session_ws != workspace_id:
        raise HTTPException(
            status_code=403,
            detail={"ok": False, "error": {"code": "FORBIDDEN", "message": "cross-workspace access denied"}},
        )
    resolved = workspace_id or session_ws
    assert resolved is not None
    return resolved


# ── List + create ───────────────────────────────────────────────────

@router.get("/v1/referrals", status_code=200)
async def list_referrals_route(
    request: Request,
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    ws = _enforce_ws(request, workspace_id)
    async with pool.acquire() as conn:
        items, total = await _repo.list_codes(
            conn, workspace_id=ws, limit=limit, offset=offset,
        )
    return _response.paginated(items, total=total, limit=limit, offset=offset)


@router.post("/v1/referrals", status_code=201)
async def create_referral_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.CreateReferralCodeBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e

    ws = _enforce_ws(request, body.workspace_id)
    state = request.state
    org_id = getattr(state, "org_id", None) or request.headers.get("x-org-id")
    user_id = getattr(state, "user_id", None) or request.headers.get("x-user-id")
    if not org_id or not user_id:
        raise HTTPException(
            status_code=401,
            detail={"ok": False, "error": {"code": "UNAUTHORIZED", "message": "session required"}},
        )

    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await _service.create_code(
                pool, conn, ctx,
                body=body, org_id=org_id, workspace_id=ws, created_by=user_id,
            )
    return _response.success(row)


@router.get("/v1/referrals/{code_id}", status_code=200)
async def get_referral_route(request: Request, code_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _repo.get_code_by_id(conn, code_id)
    if not row or not row.get("id"):
        raise _errors.AppError("PRODUCT_OPS.REFERRAL_CODE_NOT_FOUND", "not found", status_code=404)
    return _response.success(row)


@router.delete("/v1/referrals/{code_id}", status_code=204)
async def delete_referral_route(request: Request, code_id: str) -> None:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _repo.soft_delete_code(conn, code_id)


# ── Attach (anonymous-facing) + record conversion (server-facing) ──

@router.post("/v1/referrals/attach", status_code=200)
async def attach_referral_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.AttachReferralBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ctx = _build_anon_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await _service.attach_referral(pool, conn, ctx, body=body)
    return _response.success(result)


@router.post("/v1/referrals/conversions", status_code=201)
async def record_conversion_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.RecordConversionBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await _service.record_conversion(pool, conn, ctx, body=body)
    return _response.success(result)

"""HTTP routes for product_ops.promos.

  GET    /v1/promos                  — list (workspace-scoped, status filter)
  POST   /v1/promos                  — admin create
  GET    /v1/promos/{id}             — admin get
  PATCH  /v1/promos/{id}             — admin update
  DELETE /v1/promos/{id}             — soft-delete (204)
  POST   /v1/promos/redeem           — public redemption attempt (anonymous OK)
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
    "backend.02_features.10_product_ops.sub_features.05_promos.schemas"
)
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.05_promos.service"
)
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.05_promos.repository"
)

logger = logging.getLogger("tennetctl.product_ops.promos")
router = APIRouter(tags=["product_ops.promos"])


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


def _build_anon_ctx(request: Request, pool: Any) -> Any:
    del request
    return _catalog_ctx.NodeContext(
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(),
        audit_category="setup",
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
    if session_ws and workspace_id and workspace_id != session_ws:
        raise HTTPException(
            status_code=403,
            detail={"ok": False, "error": {"code": "FORBIDDEN", "message": "cross-workspace access denied"}},
        )
    resolved = workspace_id or session_ws
    assert resolved is not None
    return resolved


# ── List + create ───────────────────────────────────────────────────

@router.get("/v1/promos", status_code=200)
async def list_promos_route(
    request: Request,
    workspace_id: str | None = Query(default=None),
    status: str | None = Query(default=None, pattern="^(scheduled|active|expired|inactive|exhausted)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    ws = _enforce_ws(request, workspace_id)
    async with pool.acquire() as conn:
        items, total = await _repo.list_codes(
            conn, workspace_id=ws, status=status, limit=limit, offset=offset,
        )
    return _response.paginated(items, total=total, limit=limit, offset=offset)


@router.post("/v1/promos", status_code=201)
async def create_promo_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.CreatePromoCodeBody(**raw)
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


@router.get("/v1/promos/{promo_id}", status_code=200)
async def get_promo_route(request: Request, promo_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _repo.get_code_by_id(conn, promo_id)
    if not row or not row.get("id"):
        raise _errors.AppError("PRODUCT_OPS.PROMO_NOT_FOUND", "promo not found", status_code=404)
    return _response.success(row)


@router.patch("/v1/promos/{promo_id}", status_code=200)
async def update_promo_route(request: Request, promo_id: str) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.UpdatePromoCodeBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await _service.update_code(pool, conn, ctx, promo_id=promo_id, body=body)
    if not row:
        raise _errors.AppError("PRODUCT_OPS.PROMO_NOT_FOUND", "promo not found", status_code=404)
    return _response.success(row)


@router.delete("/v1/promos/{promo_id}", status_code=204)
async def delete_promo_route(request: Request, promo_id: str) -> None:
    pool = request.app.state.pool
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _service.delete_code(pool, conn, ctx, promo_id=promo_id)


# ── Public redemption ───────────────────────────────────────────────

@router.post("/v1/promos/redeem", status_code=200)
async def redeem_promo_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.RedeemPromoBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ctx = _build_anon_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await _service.redeem(pool, conn, ctx, body=body)
    return _response.success(result)

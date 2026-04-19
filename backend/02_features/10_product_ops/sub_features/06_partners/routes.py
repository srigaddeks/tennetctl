"""HTTP routes for product_ops.partners.

  GET    /v1/partners                     — list (workspace, tier filter)
  POST   /v1/partners                     — create
  GET    /v1/partners/{id}                — get with stats
  PATCH  /v1/partners/{id}                — update
  DELETE /v1/partners/{id}                — soft-delete (204)
  GET    /v1/partners/{id}/codes          — list linked referral + promo codes
  POST   /v1/partners/{id}/codes          — link a referral or promo code
  DELETE /v1/partners/{id}/codes/{link_id} — unlink (204)
  GET    /v1/partners/{id}/payouts        — list payouts for partner
  POST   /v1/partners/{id}/payouts        — record a payout
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
    "backend.02_features.10_product_ops.sub_features.06_partners.schemas"
)
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.06_partners.service"
)
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.06_partners.repository"
)

logger = logging.getLogger("tennetctl.product_ops.partners")
router = APIRouter(tags=["product_ops.partners"])


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
        raise HTTPException(status_code=400, detail={"ok": False, "error": {
            "code": "BAD_REQUEST", "message": "workspace_id required",
        }})
    if session_ws and workspace_id and workspace_id != session_ws:
        raise HTTPException(status_code=403, detail={"ok": False, "error": {
            "code": "FORBIDDEN", "message": "cross-workspace access denied",
        }})
    resolved = workspace_id or session_ws
    assert resolved is not None
    return resolved


def _require_session(request: Request) -> tuple[str, str]:
    state = request.state
    org_id = getattr(state, "org_id", None) or request.headers.get("x-org-id")
    user_id = getattr(state, "user_id", None) or request.headers.get("x-user-id")
    if not org_id or not user_id:
        raise HTTPException(status_code=401, detail={"ok": False, "error": {
            "code": "UNAUTHORIZED", "message": "session required",
        }})
    return org_id, user_id


# ── Partners CRUD ───────────────────────────────────────────────────

@router.get("/v1/partners", status_code=200)
async def list_partners_route(
    request: Request,
    workspace_id: str | None = Query(default=None),
    tier_code: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    ws = _enforce_ws(request, workspace_id)
    async with pool.acquire() as conn:
        items, total = await _repo.list_partners(
            conn, workspace_id=ws, tier_code=tier_code, limit=limit, offset=offset,
        )
    return _response.paginated(items, total=total, limit=limit, offset=offset)


@router.post("/v1/partners", status_code=201)
async def create_partner_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.CreatePartnerBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ws = _enforce_ws(request, body.workspace_id)
    org_id, user_id = _require_session(request)
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await _service.create_partner(
                pool, conn, ctx,
                body=body, org_id=org_id, workspace_id=ws, created_by=user_id,
            )
    return _response.success(row)


@router.get("/v1/partners/{partner_id}", status_code=200)
async def get_partner_route(request: Request, partner_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _repo.get_partner_by_id(conn, partner_id)
    if not row or not row.get("id"):
        raise _errors.AppError("PRODUCT_OPS.PARTNER_NOT_FOUND", "not found", status_code=404)
    return _response.success(row)


@router.patch("/v1/partners/{partner_id}", status_code=200)
async def update_partner_route(request: Request, partner_id: str) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.UpdatePartnerBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await _service.update_partner(pool, conn, ctx, partner_id=partner_id, body=body)
    if not row:
        raise _errors.AppError("PRODUCT_OPS.PARTNER_NOT_FOUND", "not found", status_code=404)
    return _response.success(row)


@router.delete("/v1/partners/{partner_id}", status_code=204)
async def delete_partner_route(request: Request, partner_id: str) -> None:
    pool = request.app.state.pool
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _service.delete_partner(pool, conn, ctx, partner_id=partner_id)


# ── Code linkage ────────────────────────────────────────────────────

@router.get("/v1/partners/{partner_id}/codes", status_code=200)
async def list_partner_codes_route(request: Request, partner_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _repo.list_partner_codes(conn, partner_id)
    return _response.success({"items": rows})


@router.post("/v1/partners/{partner_id}/codes", status_code=201)
async def link_partner_code_route(request: Request, partner_id: str) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.LinkCodeBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    org_id, user_id = _require_session(request)
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await _service.link_code_to_partner(
                pool, conn, ctx,
                partner_id=partner_id, body=body, org_id=org_id, created_by=user_id,
            )
    return _response.success(result)


@router.delete("/v1/partners/{partner_id}/codes/{link_id}", status_code=204)
async def unlink_partner_code_route(request: Request, partner_id: str, link_id: str) -> None:
    pool = request.app.state.pool
    del partner_id  # FK enforces ownership; the link_id alone is enough
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _repo.unlink_code(conn, link_id)


# ── Payouts ─────────────────────────────────────────────────────────

@router.get("/v1/partners/{partner_id}/payouts", status_code=200)
async def list_partner_payouts_route(request: Request, partner_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _repo.list_payouts_for_partner(conn, partner_id)
    return _response.success({"items": rows})


@router.post("/v1/partners/{partner_id}/payouts", status_code=201)
async def record_partner_payout_route(request: Request, partner_id: str) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.CreatePayoutBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    org_id, user_id = _require_session(request)
    state = request.state
    ws = getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id")
    if not ws:
        raise HTTPException(status_code=400, detail={"ok": False, "error": {
            "code": "BAD_REQUEST", "message": "workspace required",
        }})
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await _service.record_payout(
                pool, conn, ctx,
                partner_id=partner_id, body=body,
                org_id=org_id, workspace_id=ws, created_by=user_id,
            )
    return _response.success(result)

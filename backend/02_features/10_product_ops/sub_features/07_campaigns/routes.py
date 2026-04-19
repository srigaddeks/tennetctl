"""HTTP routes for product_ops.campaigns.

  GET    /v1/promo-campaigns                       — list (workspace, status filter)
  POST   /v1/promo-campaigns                       — create
  GET    /v1/promo-campaigns/{id}                  — get
  PATCH  /v1/promo-campaigns/{id}                  — update
  DELETE /v1/promo-campaigns/{id}                  — soft-delete (204)
  GET    /v1/promo-campaigns/{id}/promos           — list linked promos
  POST   /v1/promo-campaigns/{id}/promos           — link promo
  DELETE /v1/promo-campaigns/{id}/promos/{link_id} — unlink (204)
  POST   /v1/promo-campaigns/pick                  — public: pick a promo for a visitor
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
    "backend.02_features.10_product_ops.sub_features.07_campaigns.schemas"
)
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.07_campaigns.service"
)
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.07_campaigns.repository"
)

logger = logging.getLogger("tennetctl.product_ops.campaigns")
router = APIRouter(tags=["product_ops.campaigns"])


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
        raise HTTPException(status_code=400, detail={"ok": False, "error": {
            "code": "BAD_REQUEST", "message": "workspace_id required"}})
    if session_ws and workspace_id and workspace_id != session_ws:
        raise HTTPException(status_code=403, detail={"ok": False, "error": {
            "code": "FORBIDDEN", "message": "cross-workspace access denied"}})
    resolved = workspace_id or session_ws
    assert resolved is not None
    return resolved


def _require_session(request: Request) -> tuple[str, str]:
    state = request.state
    org_id = getattr(state, "org_id", None) or request.headers.get("x-org-id")
    user_id = getattr(state, "user_id", None) or request.headers.get("x-user-id")
    if not org_id or not user_id:
        raise HTTPException(status_code=401, detail={"ok": False, "error": {
            "code": "UNAUTHORIZED", "message": "session required"}})
    return org_id, user_id


# ── Campaigns CRUD ─────────────────────────────────────────────────

@router.get("/v1/promo-campaigns", status_code=200)
async def list_campaigns_route(
    request: Request,
    workspace_id: str | None = Query(default=None),
    status: str | None = Query(default=None, pattern="^(scheduled|active|ended|inactive)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    ws = _enforce_ws(request, workspace_id)
    async with pool.acquire() as conn:
        items, total = await _repo.list_campaigns(
            conn, workspace_id=ws, status=status, limit=limit, offset=offset,
        )
    return _response.paginated(items, total=total, limit=limit, offset=offset)


@router.post("/v1/promo-campaigns", status_code=201)
async def create_campaign_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.CreateCampaignBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ws = _enforce_ws(request, body.workspace_id)
    org_id, user_id = _require_session(request)
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await _service.create_campaign(
                pool, conn, ctx,
                body=body, org_id=org_id, workspace_id=ws, created_by=user_id,
            )
    return _response.success(row)


@router.get("/v1/promo-campaigns/{campaign_id}", status_code=200)
async def get_campaign_route(request: Request, campaign_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _repo.get_campaign_by_id(conn, campaign_id)
    if not row or not row.get("id"):
        raise _errors.AppError("PRODUCT_OPS.CAMPAIGN_NOT_FOUND", "not found", status_code=404)
    return _response.success(row)


@router.patch("/v1/promo-campaigns/{campaign_id}", status_code=200)
async def update_campaign_route(request: Request, campaign_id: str) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.UpdateCampaignBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await _service.update_campaign(pool, conn, ctx, campaign_id=campaign_id, body=body)
    if not row:
        raise _errors.AppError("PRODUCT_OPS.CAMPAIGN_NOT_FOUND", "not found", status_code=404)
    return _response.success(row)


@router.delete("/v1/promo-campaigns/{campaign_id}", status_code=204)
async def delete_campaign_route(request: Request, campaign_id: str) -> None:
    pool = request.app.state.pool
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _service.delete_campaign(pool, conn, ctx, campaign_id=campaign_id)


# ── Promo linkage ───────────────────────────────────────────────────

@router.get("/v1/promo-campaigns/{campaign_id}/promos", status_code=200)
async def list_campaign_promos_route(request: Request, campaign_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _repo.list_campaign_promos(conn, campaign_id)
    return _response.success({"items": rows})


@router.post("/v1/promo-campaigns/{campaign_id}/promos", status_code=201)
async def link_campaign_promo_route(request: Request, campaign_id: str) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.LinkPromoBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    org_id, user_id = _require_session(request)
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await _service.link_promo_to_campaign(
                pool, conn, ctx,
                campaign_id=campaign_id, body=body, org_id=org_id, created_by=user_id,
            )
    return _response.success(result)


@router.delete("/v1/promo-campaigns/{campaign_id}/promos/{link_id}", status_code=204)
async def unlink_campaign_promo_route(request: Request, campaign_id: str, link_id: str) -> None:
    pool = request.app.state.pool
    del campaign_id  # FK enforces ownership; link_id alone is sufficient
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _repo.unlink_promo(conn, link_id)


# ── Public picker ──────────────────────────────────────────────────

@router.post("/v1/promo-campaigns/pick", status_code=200)
async def pick_promo_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.PickPromoBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ctx = _build_anon_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await _service.pick_promo(pool, conn, ctx, body=body)
    return _response.success(result)

"""HTTP routes for product_ops.profiles.

  GET   /v1/product-profiles                — list (workspace-scoped, filters)
  POST  /v1/product-profiles/traits         — set traits on a visitor
  GET   /v1/product-profiles/{visitor_id}   — full profile (pivoted + raw traits)
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
    "backend.02_features.10_product_ops.sub_features.04_profiles.schemas"
)
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.04_profiles.service"
)
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.04_profiles.repository"
)

logger = logging.getLogger("tennetctl.product_ops.profiles")
router = APIRouter(tags=["product_ops.profiles"])


def _build_session_ctx(request: Request, pool: Any, *, audit_category: str = "user") -> Any:
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=getattr(state, "org_id", None) or request.headers.get("x-org-id"),
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", "") or _core_id.uuid7(),
        audit_category=audit_category,
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


@router.get("/v1/product-profiles", status_code=200)
async def list_profiles_route(
    request: Request,
    workspace_id: str | None = Query(default=None),
    q: str | None = Query(default=None),
    plan: str | None = Query(default=None),
    country: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    ws = _enforce_ws(request, workspace_id)
    async with pool.acquire() as conn:
        items, total = await _repo.list_profiles(
            conn,
            workspace_id=ws, q=q, plan=plan, country=country,
            limit=limit, offset=offset,
        )
    return _response.paginated(items, total=total, limit=limit, offset=offset)


@router.post("/v1/product-profiles/traits", status_code=200)
async def set_traits_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.SetTraitsBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ctx = _build_session_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await _service.set_traits(pool, conn, ctx, body=body)
    return _response.success(result)


@router.get("/v1/product-profiles/{visitor_id}", status_code=200)
async def get_profile_route(request: Request, visitor_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        profile = await _service.get_profile_full(conn, visitor_id)
    if not profile:
        raise _errors.AppError("PRODUCT_OPS.PROFILE_NOT_FOUND", "profile not found", status_code=404)
    state = request.state
    session_ws = getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id")
    if session_ws and profile["workspace_id"] != session_ws:
        raise HTTPException(
            status_code=403,
            detail={"ok": False, "error": {"code": "FORBIDDEN", "message": "cross-workspace access denied"}},
        )
    return _response.success(profile)

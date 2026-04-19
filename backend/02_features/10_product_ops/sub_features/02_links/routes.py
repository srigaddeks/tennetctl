"""HTTP routes for product_ops.links.

  GET    /l/{slug}            — public redirect (no auth; anonymous-id from cookie)
  GET    /v1/short-links      — admin list (workspace-scoped)
  POST   /v1/short-links      — admin create
  GET    /v1/short-links/{id} — admin get one
  PATCH  /v1/short-links/{id} — admin update
  DELETE /v1/short-links/{id} — admin soft-delete (204)

5-endpoint shape per ADR-026 + redirect.
"""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_schemas: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.02_links.schemas"
)
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.02_links.service"
)
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.02_links.repository"
)

logger = logging.getLogger("tennetctl.product_ops.links")
router = APIRouter(tags=["product_ops.links"])


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


def _enforce_workspace(request: Request, workspace_id: str | None) -> str:
    state = request.state
    session_ws = (
        getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id")
    )
    if session_ws is None and workspace_id is None:
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "error": {"code": "BAD_REQUEST", "message": "workspace_id required"}},
        )
    if session_ws is not None and workspace_id is not None and workspace_id != session_ws:
        raise HTTPException(
            status_code=403,
            detail={"ok": False, "error": {"code": "FORBIDDEN", "message": "cross-workspace access denied"}},
        )
    resolved = workspace_id or session_ws
    assert resolved is not None
    return resolved


def _enforce_workspace_for_id(request: Request, link: dict) -> None:
    state = request.state
    session_ws = (
        getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id")
    )
    if session_ws and link["workspace_id"] != session_ws:
        raise HTTPException(
            status_code=403,
            detail={"ok": False, "error": {"code": "FORBIDDEN", "message": "cross-workspace access denied"}},
        )


# ── Public redirect ─────────────────────────────────────────────────

@router.get("/l/{slug}")
async def redirect_route(request: Request, slug: str) -> Any:
    pool = request.app.state.pool
    workspace_id = request.headers.get("x-workspace-id") or request.query_params.get("ws")
    if not workspace_id:
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "error": {"code": "BAD_REQUEST", "message": "workspace_id (X-Workspace-Id or ?ws=) required for redirect"}},
        )

    visitor_aid = request.cookies.get("tnt_vid") or request.cookies.get("tnt_vid_fallback")

    ctx = _catalog_ctx.NodeContext(
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(),
        audit_category="setup",
        extras={"pool": pool},
    )

    async with pool.acquire() as conn:
        link = await _service.resolve_redirect(
            pool, conn, ctx,
            workspace_id=workspace_id, slug=slug, visitor_anonymous_id=visitor_aid,
        )
    if not link:
        raise HTTPException(
            status_code=404,
            detail={"ok": False, "error": {"code": "PRODUCT_OPS.LINK_NOT_FOUND", "message": f"slug {slug!r} not found"}},
        )
    return RedirectResponse(url=link["target_url"], status_code=302)


# ── Admin CRUD ──────────────────────────────────────────────────────

@router.get("/v1/short-links", status_code=200)
async def list_links_route(
    request: Request,
    workspace_id: str | None = Query(default=None),
    include_deleted: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    ws = _enforce_workspace(request, workspace_id)
    async with pool.acquire() as conn:
        items, total = await _repo.list_short_links(
            conn, workspace_id=ws, include_deleted=include_deleted,
            limit=limit, offset=offset,
        )
    return _response.paginated(items, total=total, limit=limit, offset=offset)


@router.post("/v1/short-links", status_code=201)
async def create_link_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.CreateShortLinkBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e

    ws = _enforce_workspace(request, body.workspace_id)
    state = request.state
    org_id = getattr(state, "org_id", None) or request.headers.get("x-org-id")
    user_id = getattr(state, "user_id", None) or request.headers.get("x-user-id")
    if not org_id or not user_id:
        raise HTTPException(
            status_code=401,
            detail={"ok": False, "error": {"code": "UNAUTHORIZED", "message": "session required"}},
        )

    ctx = _build_session_ctx(request, pool, audit_category="user")
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await _service.create_link(
                pool, conn, ctx,
                body=body, org_id=org_id, workspace_id=ws, created_by=user_id,
            )
    return _response.success(row)


@router.get("/v1/short-links/{link_id}", status_code=200)
async def get_link_route(request: Request, link_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _repo.get_short_link_by_id(conn, link_id)
    if not row:
        raise _errors.AppError("PRODUCT_OPS.LINK_NOT_FOUND", "link not found", status_code=404)
    _enforce_workspace_for_id(request, row)
    return _response.success(row)


@router.patch("/v1/short-links/{link_id}", status_code=200)
async def update_link_route(request: Request, link_id: str) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.UpdateShortLinkBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e

    ctx = _build_session_ctx(request, pool, audit_category="user")
    async with pool.acquire() as conn:
        existing = await _repo.get_short_link_by_id(conn, link_id)
        if not existing:
            raise _errors.AppError("PRODUCT_OPS.LINK_NOT_FOUND", "link not found", status_code=404)
        _enforce_workspace_for_id(request, existing)
        async with conn.transaction():
            row = await _service.update_link(pool, conn, ctx, link_id=link_id, body=body)
    return _response.success(row)


@router.delete("/v1/short-links/{link_id}", status_code=204)
async def delete_link_route(request: Request, link_id: str) -> None:
    pool = request.app.state.pool
    ctx = _build_session_ctx(request, pool, audit_category="user")
    async with pool.acquire() as conn:
        existing = await _repo.get_short_link_by_id(conn, link_id)
        if not existing:
            raise _errors.AppError("PRODUCT_OPS.LINK_NOT_FOUND", "link not found", status_code=404)
        _enforce_workspace_for_id(request, existing)
        async with conn.transaction():
            await _service.delete_link(pool, conn, ctx, link_id=link_id)
    # FastAPI: 204 must not return body

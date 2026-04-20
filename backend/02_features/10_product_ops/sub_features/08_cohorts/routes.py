"""HTTP routes for product_ops.cohorts.

  GET    /v1/cohorts                    — list (workspace, kind filter)
  POST   /v1/cohorts                    — create
  GET    /v1/cohorts/{id}               — get
  PATCH  /v1/cohorts/{id}               — update
  DELETE /v1/cohorts/{id}               — soft-delete (204)
  POST   /v1/cohorts/{id}/refresh       — re-evaluate dynamic cohort
  GET    /v1/cohorts/{id}/members       — list resolved members
  POST   /v1/cohorts/{id}/members       — add visitor_ids (static cohorts only)
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
    "backend.02_features.10_product_ops.sub_features.08_cohorts.schemas"
)
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.08_cohorts.service"
)
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.08_cohorts.repository"
)

logger = logging.getLogger("tennetctl.product_ops.cohorts")
router = APIRouter(tags=["product_ops.cohorts"])


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


@router.get("/v1/cohorts", status_code=200)
async def list_cohorts_route(
    request: Request,
    workspace_id: str | None = Query(default=None),
    kind: str | None = Query(default=None, pattern="^(dynamic|static)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    ws = _enforce_ws(request, workspace_id)
    async with pool.acquire() as conn:
        items, total = await _repo.list_cohorts(
            conn, workspace_id=ws, kind=kind, limit=limit, offset=offset,
        )
    return _response.paginated(items, total=total, limit=limit, offset=offset)


@router.post("/v1/cohorts", status_code=201)
async def create_cohort_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.CreateCohortBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ws = _enforce_ws(request, body.workspace_id)
    org_id, user_id = _require_session(request)
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await _service.create_cohort(
                pool, conn, ctx,
                body=body, org_id=org_id, workspace_id=ws, created_by=user_id,
            )
    return _response.success(row)


@router.get("/v1/cohorts/{cohort_id}", status_code=200)
async def get_cohort_route(request: Request, cohort_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _repo.get_cohort_by_id(conn, cohort_id)
    if not row or not row.get("id"):
        raise _errors.AppError("PRODUCT_OPS.COHORT_NOT_FOUND", "not found", status_code=404)
    return _response.success(row)


@router.patch("/v1/cohorts/{cohort_id}", status_code=200)
async def update_cohort_route(request: Request, cohort_id: str) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.UpdateCohortBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await _service.update_cohort(pool, conn, ctx, cohort_id=cohort_id, body=body)
    if not row:
        raise _errors.AppError("PRODUCT_OPS.COHORT_NOT_FOUND", "not found", status_code=404)
    return _response.success(row)


@router.delete("/v1/cohorts/{cohort_id}", status_code=204)
async def delete_cohort_route(request: Request, cohort_id: str) -> None:
    pool = request.app.state.pool
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _service.delete_cohort(pool, conn, ctx, cohort_id=cohort_id)


@router.post("/v1/cohorts/{cohort_id}/refresh", status_code=200)
async def refresh_cohort_route(request: Request, cohort_id: str) -> Any:
    pool = request.app.state.pool
    state = request.state
    user_id = getattr(state, "user_id", None) or request.headers.get("x-user-id")
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await _service.refresh_cohort(
                pool, conn, ctx, cohort_id=cohort_id, triggered_by=user_id,
            )
    return _response.success(result)


@router.get("/v1/cohorts/{cohort_id}/members", status_code=200)
async def list_cohort_members_route(
    request: Request, cohort_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items, total = await _repo.list_members(conn, cohort_id, limit=limit, offset=offset)
    return _response.paginated(items, total=total, limit=limit, offset=offset)


@router.post("/v1/cohorts/{cohort_id}/members", status_code=200)
async def add_cohort_members_route(request: Request, cohort_id: str) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.AddMembersBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await _service.add_static_members(
                pool, conn, ctx, cohort_id=cohort_id, visitor_ids=body.visitor_ids,
            )
    return _response.success(result)

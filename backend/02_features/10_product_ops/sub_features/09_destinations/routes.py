"""HTTP routes for product_ops.destinations.

  GET    /v1/destinations                       — list (workspace, kind filter)
  POST   /v1/destinations                       — create (operator)
  GET    /v1/destinations/{id}                  — get (no secret)
  PATCH  /v1/destinations/{id}                  — update
  DELETE /v1/destinations/{id}                  — soft-delete (204)
  POST   /v1/destinations/{id}/test             — send synthetic event
  GET    /v1/destinations/{id}/deliveries       — recent delivery log
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
    "backend.02_features.10_product_ops.sub_features.09_destinations.schemas"
)
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.09_destinations.service"
)
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.09_destinations.repository"
)

logger = logging.getLogger("tennetctl.product_ops.destinations")
router = APIRouter(tags=["product_ops.destinations"])


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


@router.get("/v1/destinations", status_code=200)
async def list_destinations_route(
    request: Request,
    workspace_id: str | None = Query(default=None),
    kind: str | None = Query(default=None, pattern="^(webhook|slack|custom)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    ws = _enforce_ws(request, workspace_id)
    async with pool.acquire() as conn:
        items, total = await _repo.list_destinations(
            conn, workspace_id=ws, kind=kind, limit=limit, offset=offset,
        )
    return _response.paginated(items, total=total, limit=limit, offset=offset)


@router.post("/v1/destinations", status_code=201)
async def create_destination_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.CreateDestinationBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ws = _enforce_ws(request, body.workspace_id)
    org_id, user_id = _require_session(request)
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await _service.create_destination(
                pool, conn, ctx,
                body=body, org_id=org_id, workspace_id=ws, created_by=user_id,
            )
    return _response.success(row)


@router.get("/v1/destinations/{dest_id}", status_code=200)
async def get_destination_route(request: Request, dest_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _repo.get_destination_by_id(conn, dest_id)
    if not row or not row.get("id"):
        raise _errors.AppError("PRODUCT_OPS.DESTINATION_NOT_FOUND", "not found", status_code=404)
    return _response.success(row)


@router.patch("/v1/destinations/{dest_id}", status_code=200)
async def update_destination_route(request: Request, dest_id: str) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    try:
        body = _schemas.UpdateDestinationBody(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await _service.update_destination(pool, conn, ctx, dest_id=dest_id, body=body)
    if not row:
        raise _errors.AppError("PRODUCT_OPS.DESTINATION_NOT_FOUND", "not found", status_code=404)
    return _response.success(row)


@router.delete("/v1/destinations/{dest_id}", status_code=204)
async def delete_destination_route(request: Request, dest_id: str) -> None:
    pool = request.app.state.pool
    ctx = _build_session_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _service.delete_destination(pool, conn, ctx, dest_id=dest_id)


@router.post("/v1/destinations/{dest_id}/test", status_code=200)
async def test_destination_route(request: Request, dest_id: str) -> Any:
    pool = request.app.state.pool
    raw = {}
    try:
        raw = await request.json()
    except Exception:
        pass
    body = _schemas.TestDestinationBody(**(raw or {}))
    async with pool.acquire() as conn:
        result = await _service.test_destination(
            pool, conn, dest_id=dest_id, sample_event=body.sample_event,
        )
    return _response.success(result)


@router.get("/v1/destinations/{dest_id}/deliveries", status_code=200)
async def list_deliveries_route(
    request: Request, dest_id: str,
    status: str | None = Query(default=None, pattern="^(pending|success|failure|timeout|rejected_filter)$"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items, total = await _repo.list_deliveries(
            conn, dest_id, status=status, limit=limit, offset=offset,
        )
    return _response.paginated(items, total=total, limit=limit, offset=offset)

"""Routes for monitoring.saved_queries — CRUD + run."""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request, Response

_errors: Any = import_module("backend.01_core.errors")
_resp: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.04_saved_queries.schemas"
)
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.04_saved_queries.service"
)

SavedQueryCreateRequest = _schemas.SavedQueryCreateRequest
SavedQueryUpdateRequest = _schemas.SavedQueryUpdateRequest
SavedQueryResponse = _schemas.SavedQueryResponse
SavedQueryListResponse = _schemas.SavedQueryListResponse

router = APIRouter(tags=["monitoring.saved_queries"])


def _scope(request: Request) -> tuple[str, str]:
    state = request.state
    org_id = getattr(state, "org_id", None) or request.headers.get("x-org-id")
    user_id = getattr(state, "user_id", None) or request.headers.get("x-user-id")
    if not org_id:
        raise _errors.AppError("UNAUTHORIZED", "org_id required", 401)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "user_id required", 401)
    return org_id, user_id


def _build_ctx(request: Request) -> Any:
    org_id, user_id = _scope(request)
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=user_id,
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=org_id,
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", "") or _core_id.uuid7(),
        audit_category="system",
    )


@router.post("/v1/monitoring/saved-queries", status_code=201)
async def create_saved_query_route(
    request: Request, body: SavedQueryCreateRequest
) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    async with pool.acquire() as conn:
        row = await _service.create(
            conn,
            org_id=org_id,
            owner_user_id=user_id,
            name=body.name,
            description=body.description,
            target=body.target,
            dsl=body.dsl,
            shared=body.shared,
        )
    return _resp.success(SavedQueryResponse.from_row(row).model_dump())


@router.get("/v1/monitoring/saved-queries", status_code=200)
async def list_saved_queries_route(
    request: Request,
    target: str | None = Query(default=None, pattern="^(logs|metrics|traces)$"),
) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    async with pool.acquire() as conn:
        rows = await _service.list_for_user(
            conn, org_id=org_id, user_id=user_id, target=target,
        )
    items = [SavedQueryResponse.from_row(r).model_dump() for r in rows]
    return _resp.success({"items": items, "total": len(items)})


@router.get("/v1/monitoring/saved-queries/{id}", status_code=200)
async def get_saved_query_route(request: Request, id: str) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    async with pool.acquire() as conn:
        row = await _service.get(conn, org_id=org_id, user_id=user_id, id=id)
    if row is None:
        raise _errors.NotFoundError(f"saved query {id!r} not found")
    return _resp.success(SavedQueryResponse.from_row(row).model_dump())


@router.patch("/v1/monitoring/saved-queries/{id}", status_code=200)
async def update_saved_query_route(
    request: Request, id: str, body: SavedQueryUpdateRequest
) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    async with pool.acquire() as conn:
        row = await _service.update(
            conn,
            org_id=org_id, user_id=user_id, id=id,
            name=body.name, description=body.description,
            dsl=body.dsl, shared=body.shared, is_active=body.is_active,
        )
    if row is None:
        raise _errors.NotFoundError(f"saved query {id!r} not found")
    return _resp.success(SavedQueryResponse.from_row(row).model_dump())


@router.delete(
    "/v1/monitoring/saved-queries/{id}",
    status_code=204,
    response_class=Response,
)
async def delete_saved_query_route(request: Request, id: str) -> Response:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    async with pool.acquire() as conn:
        ok = await _service.delete(conn, org_id=org_id, user_id=user_id, id=id)
    if not ok:
        raise _errors.NotFoundError(f"saved query {id!r} not found")
    return Response(status_code=204)


@router.post("/v1/monitoring/saved-queries/{id}/run", status_code=200)
async def run_saved_query_route(request: Request, id: str) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        result = await _service.run(conn, ctx, id=id)
    return _resp.success(result)

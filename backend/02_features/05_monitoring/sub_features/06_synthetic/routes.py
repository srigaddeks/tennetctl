"""Routes for monitoring.synthetic — 5-endpoint CRUD."""

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
    "backend.02_features.05_monitoring.sub_features.06_synthetic.schemas"
)
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.06_synthetic.service"
)

SyntheticCheckCreateRequest = _schemas.SyntheticCheckCreateRequest
SyntheticCheckUpdateRequest = _schemas.SyntheticCheckUpdateRequest
SyntheticCheckResponse = _schemas.SyntheticCheckResponse

router = APIRouter(tags=["monitoring.synthetic"])


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
        application_id=getattr(state, "application_id", None) or request.headers.get("x-application-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", "") or _core_id.uuid7(),
        audit_category="system",
    )


@router.post("/v1/monitoring/synthetic-checks", status_code=201)
async def create_synthetic_check_route(
    request: Request, body: SyntheticCheckCreateRequest,
) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.create(
            conn, ctx, pool,
            org_id=org_id,
            name=body.name,
            target_url=body.target_url,
            method=body.method,
            expected_status=body.expected_status,
            timeout_ms=body.timeout_ms,
            interval_seconds=body.interval_seconds,
            headers=body.headers,
            body=body.body,
            assertions=body.assertions,
        )
    return _resp.success(SyntheticCheckResponse.from_row(row).model_dump())


@router.get("/v1/monitoring/synthetic-checks", status_code=200)
async def list_synthetic_checks_route(
    request: Request,
    is_active: bool | None = Query(default=None),
) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    async with pool.acquire() as conn:
        rows = await _service.list_checks(conn, org_id=org_id, is_active=is_active)
    items = [SyntheticCheckResponse.from_row(r).model_dump() for r in rows]
    return _resp.success({"items": items, "total": len(items)})


@router.get("/v1/monitoring/synthetic-checks/{id}", status_code=200)
async def get_synthetic_check_route(request: Request, id: str) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    async with pool.acquire() as conn:
        row = await _service.get(conn, org_id=org_id, id=id)
    if row is None:
        raise _errors.NotFoundError(f"synthetic check {id!r} not found")
    return _resp.success(SyntheticCheckResponse.from_row(row).model_dump())


@router.patch("/v1/monitoring/synthetic-checks/{id}", status_code=200)
async def update_synthetic_check_route(
    request: Request, id: str, body: SyntheticCheckUpdateRequest,
) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.update(
            conn, ctx, pool,
            org_id=org_id, id=id,
            name=body.name, target_url=body.target_url, method=body.method,
            expected_status=body.expected_status, timeout_ms=body.timeout_ms,
            interval_seconds=body.interval_seconds, headers=body.headers,
            body=body.body, assertions=body.assertions, is_active=body.is_active,
        )
    if row is None:
        raise _errors.NotFoundError(f"synthetic check {id!r} not found")
    return _resp.success(SyntheticCheckResponse.from_row(row).model_dump())


@router.delete(
    "/v1/monitoring/synthetic-checks/{id}",
    status_code=204,
    response_class=Response,
)
async def delete_synthetic_check_route(request: Request, id: str) -> Response:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        ok = await _service.delete(conn, ctx, pool, org_id=org_id, id=id)
    if not ok:
        raise _errors.NotFoundError(f"synthetic check {id!r} not found")
    return Response(status_code=204)

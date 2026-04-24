"""Routes for monitoring.metrics — registry CRUD + ingest endpoints."""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Body, Request

_errors: Any = import_module("backend.01_core.errors")
_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_schemas: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.02_metrics.schemas"
)
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.02_metrics.service"
)
_resp: Any = import_module("backend.01_core.response")
_dsl: Any = import_module("backend.02_features.05_monitoring.query_dsl")

MetricRegisterRequest = _schemas.MetricRegisterRequest
MetricIncrementRequest = _schemas.MetricIncrementRequest
MetricSetRequest = _schemas.MetricSetRequest
MetricObserveRequest = _schemas.MetricObserveRequest
MetricResponse = _schemas.MetricResponse

router = APIRouter(tags=["monitoring.metrics"])


def _build_ctx(request: Request, pool: Any, *, audit_category: str = "setup") -> Any:
    """Metrics mutations run at org scope (no workspace); audit_category='setup' bypasses
    the workspace_id requirement in chk_evt_audit_scope on register audit events.
    """
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        session_id=(
            getattr(state, "session_id", None) or request.headers.get("x-session-id")
        ),
        org_id=getattr(state, "org_id", None) or request.headers.get("x-org-id"),
        workspace_id=(
            getattr(state, "workspace_id", None)
            or request.headers.get("x-workspace-id")
        ),
        application_id=getattr(state, "application_id", None) or request.headers.get("x-application-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=(
            getattr(state, "request_id", None) or _core_id.uuid7()
        ),
        audit_category=audit_category,
        pool=pool,
        extras={"pool": pool},
    )


def _resolve_org_id(request: Request, body_org_id: str | None = None) -> str:
    org_id = (
        body_org_id
        or getattr(request.state, "org_id", None)
        or request.headers.get("x-org-id")
    )
    if not org_id:
        raise _errors.AppError(
            "UNAUTHORIZED",
            "org_id is required (via session, x-org-id header, or request body).",
            401,
        )
    return org_id


@router.post("/v1/monitoring/metrics", status_code=201)
async def register_metric_route(
    request: Request, body: MetricRegisterRequest
) -> dict:
    pool = request.app.state.pool
    org_id = _resolve_org_id(request)
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        row = await _service.register_metric(
            conn, pool, ctx2, org_id=org_id, req=body,
        )
    return _response.success(MetricResponse.from_row(row).model_dump())


@router.get("/v1/monitoring/metrics", status_code=200)
async def list_metrics_route(request: Request) -> dict:
    pool = request.app.state.pool
    org_id = _resolve_org_id(request)
    async with pool.acquire() as conn:
        rows = await _service.list_metrics(conn, org_id=org_id)
    items = [MetricResponse.from_row(r).model_dump() for r in rows]
    return _response.success({"items": items, "total": len(items)})


@router.get("/v1/monitoring/metrics/{key}", status_code=200)
async def get_metric_route(request: Request, key: str) -> dict:
    pool = request.app.state.pool
    org_id = _resolve_org_id(request)
    async with pool.acquire() as conn:
        row = await _service.get_metric(conn, org_id=org_id, key=key)
    if row is None:
        raise _errors.NotFoundError(f"metric {key!r} not found")
    return _response.success(MetricResponse.from_row(row).model_dump())


@router.post("/v1/monitoring/metrics/{key}/increment", status_code=201)
async def increment_metric_route(
    request: Request, key: str, body: MetricIncrementRequest
) -> dict:
    pool = request.app.state.pool
    org_id = _resolve_org_id(request)
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        result = await _service.increment(
            conn, pool, ctx2, org_id=org_id, key=key, req=body,
        )
    return _response.success(result)


@router.post("/v1/monitoring/metrics/{key}/set", status_code=201)
async def set_gauge_route(
    request: Request, key: str, body: MetricSetRequest
) -> dict:
    pool = request.app.state.pool
    org_id = _resolve_org_id(request)
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        result = await _service.set_gauge(
            conn, pool, ctx2, org_id=org_id, key=key, req=body,
        )
    return _response.success(result)


@router.post("/v1/monitoring/metrics/query", status_code=200)
async def metrics_query_route(request: Request, body: dict = Body(...)) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool)
    try:
        async with pool.acquire() as conn:
            ctx2 = replace(ctx_base, conn=conn)
            items, next_cursor = await _service.query(conn, ctx2, body)
    except _dsl.InvalidQueryError as e:
        raise _errors.AppError("INVALID_QUERY", str(e), 400) from e
    return _response.success({"items": items, "next_cursor": next_cursor})


@router.post("/v1/monitoring/metrics/{key}/observe", status_code=201)
async def observe_histogram_route(
    request: Request, key: str, body: MetricObserveRequest
) -> dict:
    pool = request.app.state.pool
    org_id = _resolve_org_id(request)
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        result = await _service.observe_histogram(
            conn, pool, ctx2, org_id=org_id, key=key, req=body,
        )
    return _response.success(result)

"""OTLP/HTTP traces receiver.

POST /v1/monitoring/otlp/v1/traces
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from dataclasses import replace

from fastapi import APIRouter, Body, Header, HTTPException, Request, Response
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    ExportTracePartialSuccess,
    ExportTraceServiceResponse,
)
from google.protobuf.json_format import MessageToJson  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]

_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.03_traces.service"
)
publish_traces_batch = _service.publish_traces_batch

_nats_core: Any = import_module("backend.01_core.nats")
_config_mod: Any = import_module("backend.01_core.config")
_errors: Any = import_module("backend.01_core.errors")
_resp: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_dsl: Any = import_module("backend.02_features.05_monitoring.query_dsl")
_rate: Any = import_module("backend.01_core.rate_limit")

router = APIRouter(prefix="/v1/monitoring", tags=["monitoring.traces"])

# Traces are spikier than logs at trace-emit time. Allow a larger burst.
_otlp_traces_limiter = _rate.TokenBucketLimiter(capacity=600.0, refill_per_sec=300.0)


def _build_response(rejected: int, content_type: str) -> Response:
    resp = ExportTraceServiceResponse()
    if rejected > 0:
        resp.partial_success.CopyFrom(
            ExportTracePartialSuccess(rejected_spans=rejected)
        )
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype == "application/json":
        body = MessageToJson(resp, preserving_proto_field_name=False).encode("utf-8")
        media = "application/json"
    else:
        body = resp.SerializeToString()
        media = "application/x-protobuf"
    status = 400 if rejected > 0 else 200
    return Response(content=body, media_type=media, status_code=status)


def _check_auth(authorization: str | None) -> None:
    config = _config_mod.load_config()
    if not getattr(config, "monitoring_otlp_auth_enabled", False):
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/otlp/v1/traces")
async def otlp_traces(
    request: Request,
    authorization: str | None = Header(default=None),
) -> Response:
    _check_auth(authorization)
    key = _rate.client_key(request, prefix="otlp.traces")
    if not await _otlp_traces_limiter.acquire(key):
        raise HTTPException(status_code=429, detail="rate_limited")
    body = await request.body()
    content_type = request.headers.get("content-type", "application/x-protobuf")

    js = _nats_core.get_js()
    _, rejected = await publish_traces_batch(body, content_type, js)
    return _build_response(rejected, content_type)


def _build_query_ctx(request: Request) -> Any:
    state = request.state
    org_id = getattr(state, "org_id", None) or request.headers.get("x-org-id")
    if not org_id:
        raise _errors.AppError("UNAUTHORIZED", "org_id required (session or x-org-id header)", 401)
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=org_id,
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        application_id=getattr(state, "application_id", None) or request.headers.get("x-application-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", "") or _core_id.uuid7(),
        audit_category="system",
    )


@router.post("/traces/query")
async def traces_query_route(request: Request, body: dict = Body(...)) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_query_ctx(request)
    try:
        async with pool.acquire() as conn:
            ctx = replace(ctx_base, conn=conn)
            items, next_cursor = await _service.query(conn, ctx, body)
    except _dsl.InvalidQueryError as e:
        raise _errors.AppError("INVALID_QUERY", str(e), 400) from e
    return _resp.success({"items": items, "next_cursor": next_cursor})


@router.get("/traces/{trace_id}")
async def trace_detail_route(request: Request, trace_id: str) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_query_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        spans = await _service.get_trace(conn, ctx, trace_id)
    return _resp.success({"trace_id": trace_id, "spans": spans})

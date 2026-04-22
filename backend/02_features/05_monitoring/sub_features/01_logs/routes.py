"""OTLP/HTTP logs receiver.

POST /v1/monitoring/otlp/v1/logs
  Content-Type: application/x-protobuf | application/json

Publishes each ResourceLogs to JetStream subject ``monitoring.logs.otel.{service}``.
Returns an OTLP ExportLogsServiceResponse (protobuf or JSON, matching request
content-type). No tennetctl envelope — public OTel contract.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from dataclasses import replace

from fastapi import APIRouter, Body, Header, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from opentelemetry.proto.collector.logs.v1.logs_service_pb2 import (  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
    ExportLogsPartialSuccess,
    ExportLogsServiceResponse,
)
from google.protobuf.json_format import MessageToJson  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]

_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.01_logs.service"
)
publish_logs_batch = _service.publish_logs_batch

_nats_core: Any = import_module("backend.01_core.nats")
_config_mod: Any = import_module("backend.01_core.config")
_errors: Any = import_module("backend.01_core.errors")
_resp: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_dsl: Any = import_module("backend.02_features.05_monitoring.query_dsl")
_rate: Any = import_module("backend.01_core.rate_limit")

router = APIRouter(prefix="/v1/monitoring", tags=["monitoring.logs"])

# Per-source token bucket for OTLP intake. Sized for busy agents while still
# shedding runaway producers: 200 requests/sec steady-state, 400 req burst.
_otlp_logs_limiter = _rate.TokenBucketLimiter(capacity=400.0, refill_per_sec=200.0)


def _build_response(rejected: int, content_type: str) -> Response:
    """Build ExportLogsServiceResponse matching the request content-type."""
    resp = ExportLogsServiceResponse()
    if rejected > 0:
        resp.partial_success.CopyFrom(
            ExportLogsPartialSuccess(rejected_log_records=rejected)
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
    """Stub bearer auth: when flag enabled, require a bearer token header.

    Full vault lookup deferred — plan 13-03 scope: stub returns 401 when
    flag is on and header missing/malformed.
    """
    config = _config_mod.load_config()
    if not getattr(config, "monitoring_otlp_auth_enabled", False):
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/otlp/v1/logs")
async def otlp_logs(
    request: Request,
    authorization: str | None = Header(default=None),
) -> Response:
    """OTLP/HTTP logs ingest endpoint."""
    _check_auth(authorization)
    key = _rate.client_key(request, prefix="otlp.logs")
    if not await _otlp_logs_limiter.acquire(key):
        raise HTTPException(status_code=429, detail="rate_limited")
    body = await request.body()
    content_type = request.headers.get("content-type", "application/x-protobuf")

    js = _nats_core.get_js()
    _, rejected = await publish_logs_batch(body, content_type, js)
    return _build_response(rejected, content_type)


def _build_query_ctx(request: Request) -> Any:
    state = request.state
    org_id = (
        getattr(state, "org_id", None) or request.headers.get("x-org-id")
    )
    if not org_id:
        raise _errors.AppError(
            "UNAUTHORIZED",
            "org_id required (session or x-org-id header)",
            401,
        )
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=org_id,
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", "") or _core_id.uuid7(),
        audit_category="system",
    )


@router.post("/logs/query")
async def logs_query_route(request: Request, body: dict = Body(...)) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_query_ctx(request)
    # Enforce cross-org: if caller passes `org_id` in filter it must match ctx.
    try:
        async with pool.acquire() as conn:
            ctx = replace(ctx_base, conn=conn)
            items, next_cursor = await _service.query(conn, ctx, body)
    except _dsl.InvalidQueryError as e:
        raise _errors.AppError("INVALID_QUERY", str(e), 400) from e
    return _resp.success({"items": items, "next_cursor": next_cursor})


# ---------------------------------------------------------------------------
# SSE live-tail — GET /v1/monitoring/logs/tail
# ---------------------------------------------------------------------------

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _decode_filter(filter_b64: str | None) -> dict[str, Any] | None:
    if not filter_b64:
        return None
    import base64 as _b64
    import json as _json
    try:
        raw = _b64.urlsafe_b64decode(filter_b64.encode("ascii") + b"==")
        parsed = _json.loads(raw.decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        raise _errors.AppError("INVALID_FILTER", f"filter_b64 decode failed: {e}", 400) from e
    if not isinstance(parsed, dict):
        raise _errors.AppError("INVALID_FILTER", "filter_b64 must decode to object", 400)
    return parsed


async def _tail_generator(
    pool: Any,
    org_id: str,
    dsl_filter: dict[str, Any] | None,
    poll_interval_s: float = 1.0,
    heartbeat_interval_s: float = 15.0,
    max_batch: int = 100,
    drop_threshold: int = 500,
):
    """Async generator that yields SSE-formatted events.

    Polls v_monitoring_logs for new rows strictly after the last (recorded_at, id)
    cursor every `poll_interval_s`. Emits a `: keepalive\\n\\n` comment every
    `heartbeat_interval_s` when there is no new data. If more than
    `drop_threshold` rows are pending between polls, older ones are dropped
    and a `event: dropped\\ndata: {"count":N}\\n\\n` marker is emitted.
    """
    import asyncio as _asyncio
    import json as _json
    from datetime import datetime, timezone

    # Validate filter (best-effort — DSL is the logs DSL when provided).
    if dsl_filter is not None:
        try:
            _dsl.validate_logs_query({
                "target": "logs",
                "timerange": {"last": "1h"},
                **{k: v for k, v in dsl_filter.items() if k not in ("timerange", "target")},
            })
        except _dsl.InvalidQueryError as e:
            raise _errors.AppError("INVALID_FILTER", str(e), 400) from e

    last_ts: datetime | None = datetime.now(timezone.utc).replace(tzinfo=None)
    last_id: str | None = None
    last_activity = _asyncio.get_event_loop().time()

    # Emit an initial comment so the client receives response headers + starts
    # consuming immediately (before the first DB poll).
    yield b": ready\n\n"

    body_contains = None
    severity_min = None
    service_name = None
    if dsl_filter is not None:
        body_contains = dsl_filter.get("body_contains")
        severity_min = dsl_filter.get("severity_min")
        service_name = dsl_filter.get("service_name")

    try:
        while True:
            # Build SQL dynamically.
            where_parts = ['org_id = $1', '(recorded_at, id) > ($2, $3)']
            params: list[Any] = [org_id, last_ts, last_id or ""]
            if severity_min is not None:
                params.append(int(severity_min))
                where_parts.append(f"severity_id >= ${len(params)}")
            if service_name is not None:
                params.append(str(service_name))
                where_parts.append(f"service_name = ${len(params)}")
            if body_contains is not None:
                params.append(f"%{body_contains}%")
                where_parts.append(f"body ILIKE ${len(params)}")
            sql = f"""
                SELECT id, org_id, workspace_id, service_name, recorded_at,
                       severity_id, severity_code, severity_text, body,
                       trace_id, span_id, attributes
                  FROM "05_monitoring"."v_monitoring_logs"
                 WHERE {' AND '.join(where_parts)}
                 ORDER BY recorded_at ASC, id ASC
                 LIMIT {drop_threshold + 1}
            """

            async with pool.acquire() as conn:
                rows = await conn.fetch(sql, *params)

            if rows:
                if len(rows) > drop_threshold:
                    dropped = len(rows) - max_batch
                    rows = rows[-max_batch:]
                    yield (
                        f"event: dropped\ndata: "
                        f"{_json.dumps({'count': dropped})}\n\n"
                    ).encode("utf-8")
                for r in rows:
                    row = dict(r)
                    last_ts = row.get("recorded_at") or last_ts
                    last_id = row.get("id") or last_id
                    yield (
                        f"data: {_json.dumps(row, default=str)}\n\n"
                    ).encode("utf-8")
                last_activity = _asyncio.get_event_loop().time()
            else:
                now = _asyncio.get_event_loop().time()
                if now - last_activity >= heartbeat_interval_s:
                    yield b": keepalive\n\n"
                    last_activity = now

            await _asyncio.sleep(poll_interval_s)
    except _asyncio.CancelledError:
        return


async def _notify_tail_generator(
    pool: Any,
    listener: Any,
    org_id: str,
    dsl_filter: dict[str, Any] | None,
    heartbeat_interval_s: float = 15.0,
):
    """LISTEN/NOTIFY-backed tail generator.

    Subscribes to the NotifyListener broadcaster; for each payload, scopes by
    org_id and fetches the full row, yielding SSE data. Falls back on asyncio
    timeouts to send heartbeats.
    """
    import asyncio as _asyncio
    import json as _json

    body_contains = None
    severity_min = None
    service_name = None
    if dsl_filter is not None:
        body_contains = dsl_filter.get("body_contains")
        severity_min = dsl_filter.get("severity_min")
        service_name = dsl_filter.get("service_name")

    q = listener.broadcaster.subscribe()
    yield b": ready\n\n"
    try:
        while True:
            try:
                payload = await _asyncio.wait_for(q.get(), timeout=heartbeat_interval_s)
            except _asyncio.TimeoutError:
                yield b": keepalive\n\n"
                continue
            if payload.get("org_id") != org_id:
                continue
            log_id = payload.get("id")
            if not log_id:
                continue
            # Build filter SQL for optional DSL filters.
            where = ["id = $1"]
            params: list[Any] = [log_id]
            if severity_min is not None:
                params.append(int(severity_min))
                where.append(f"severity_id >= ${len(params)}")
            if service_name is not None:
                params.append(str(service_name))
                where.append(f"service_name = ${len(params)}")
            if body_contains is not None:
                params.append(f"%{body_contains}%")
                where.append(f"body ILIKE ${len(params)}")
            sql = f"""
                SELECT id, org_id, workspace_id, service_name, recorded_at,
                       severity_id, severity_code, severity_text, body,
                       trace_id, span_id, attributes
                  FROM "05_monitoring"."v_monitoring_logs"
                 WHERE {' AND '.join(where)}
                 LIMIT 1
            """
            async with pool.acquire() as conn:
                row = await conn.fetchrow(sql, *params)
            if row is None:
                continue
            yield (f"data: {_json.dumps(dict(row), default=str)}\n\n").encode("utf-8")
    except _asyncio.CancelledError:
        return
    finally:
        listener.broadcaster.unsubscribe(q)


@router.get("/logs/tail")
async def logs_tail_route(
    request: Request,
    filter_b64: str | None = None,
) -> StreamingResponse:
    """SSE live-tail of monitoring logs, scoped to ctx.org_id.

    If the NotifyListener worker is running, subscribes to its broadcaster for
    sub-100ms delivery. Otherwise falls back to 1s polling.
    """
    org_id, _user = (
        getattr(request.state, "org_id", None) or request.headers.get("x-org-id"),
        getattr(request.state, "user_id", None) or request.headers.get("x-user-id"),
    )
    if not org_id:
        raise _errors.AppError(
            "UNAUTHORIZED",
            "org_id required (session or x-org-id header)",
            401,
        )
    dsl_filter = _decode_filter(filter_b64)
    pool = request.app.state.pool

    # Prefer NotifyListener broadcaster when available.
    wp = getattr(request.app.state, "monitoring_worker_pool", None)
    listener = None
    if wp is not None:
        workers = getattr(wp, "_workers", {})
        listener = workers.get("notify_listener")
    if listener is not None and getattr(listener, "_conn", None) is not None:
        gen = _notify_tail_generator(pool, listener, org_id, dsl_filter)
    else:
        gen = _tail_generator(pool, org_id, dsl_filter)
    return StreamingResponse(
        gen,
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )

"""Routes for monitoring.alerts — rule CRUD + silences + event reads (13-08a)."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request, Response

_errors: Any = import_module("backend.01_core.errors")
_resp: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.schemas"
)
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.service"
)

AlertRuleCreateRequest = _schemas.AlertRuleCreateRequest
AlertRuleUpdateRequest = _schemas.AlertRuleUpdateRequest
AlertRulePauseRequest = _schemas.AlertRulePauseRequest
AlertRuleResponse = _schemas.AlertRuleResponse
SilenceCreateRequest = _schemas.SilenceCreateRequest
SilenceResponse = _schemas.SilenceResponse
AlertEventResponse = _schemas.AlertEventResponse

router = APIRouter(tags=["monitoring.alerts"])


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
        session_id=getattr(state, "session_id", None)
            or request.headers.get("x-session-id"),
        org_id=org_id,
        workspace_id=getattr(state, "workspace_id", None)
            or request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", "") or _core_id.uuid7(),
        audit_category="system",
    )


def _naive(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        from datetime import timezone as _tz
        dt = dt.astimezone(_tz.utc).replace(tzinfo=None)
    return dt


# ── Rule routes ───────────────────────────────────────────────────────

@router.post("/v1/monitoring/alert-rules", status_code=201)
async def create_alert_rule_route(
    request: Request, body: AlertRuleCreateRequest,
) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.create_rule(
            pool, conn, ctx,
            org_id=org_id,
            name=body.name,
            description=body.description,
            target=body.target,
            dsl=body.dsl,
            condition=body.condition.model_dump(),
            severity=body.severity,
            notify_template_key=body.notify_template_key,
            labels=body.labels,
        )
    return _resp.success(AlertRuleResponse.from_row(row).model_dump(mode="json"))


@router.get("/v1/monitoring/alert-rules", status_code=200)
async def list_alert_rules_route(
    request: Request,
    is_active: bool | None = Query(default=None),
) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        rows = await _service.list_rules(
            conn, ctx, org_id=org_id, is_active=is_active,
        )
    items = [
        AlertRuleResponse.from_row(r).model_dump(mode="json") for r in rows
    ]
    return _resp.success({"items": items, "total": len(items)})


@router.get("/v1/monitoring/alert-rules/{id}", status_code=200)
async def get_alert_rule_route(request: Request, id: str) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.get_rule(conn, ctx, org_id=org_id, rule_id=id)
    if row is None:
        raise _errors.NotFoundError(f"alert rule {id!r} not found")
    return _resp.success(AlertRuleResponse.from_row(row).model_dump(mode="json"))


@router.patch("/v1/monitoring/alert-rules/{id}", status_code=200)
async def update_alert_rule_route(
    request: Request, id: str, body: AlertRuleUpdateRequest,
) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.update_rule(
            pool, conn, ctx,
            org_id=org_id, rule_id=id,
            name=body.name,
            description=body.description,
            dsl=body.dsl,
            condition=body.condition.model_dump() if body.condition else None,
            severity=body.severity,
            notify_template_key=body.notify_template_key,
            labels=body.labels,
            is_active=body.is_active,
            paused_until=_naive(body.paused_until) if body.paused_until else None,
        )
    if row is None:
        raise _errors.NotFoundError(f"alert rule {id!r} not found")
    return _resp.success(AlertRuleResponse.from_row(row).model_dump(mode="json"))


@router.delete(
    "/v1/monitoring/alert-rules/{id}", status_code=204,
    response_class=Response,
)
async def delete_alert_rule_route(request: Request, id: str) -> Response:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        ok = await _service.delete_rule(
            pool, conn, ctx, org_id=org_id, rule_id=id,
        )
    if not ok:
        raise _errors.NotFoundError(f"alert rule {id!r} not found")
    return Response(status_code=204)


@router.post("/v1/monitoring/alert-rules/{id}/pause", status_code=200)
async def pause_alert_rule_route(
    request: Request, id: str, body: AlertRulePauseRequest,
) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.pause_rule(
            pool, conn, ctx,
            org_id=org_id, rule_id=id,
            paused_until=_naive(body.paused_until),
        )
    if row is None:
        raise _errors.NotFoundError(f"alert rule {id!r} not found")
    return _resp.success(AlertRuleResponse.from_row(row).model_dump(mode="json"))


@router.post("/v1/monitoring/alert-rules/{id}/unpause", status_code=200)
async def unpause_alert_rule_route(request: Request, id: str) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.unpause_rule(
            pool, conn, ctx, org_id=org_id, rule_id=id,
        )
    if row is None:
        raise _errors.NotFoundError(f"alert rule {id!r} not found")
    return _resp.success(AlertRuleResponse.from_row(row).model_dump(mode="json"))


# ── Silence routes ────────────────────────────────────────────────────

@router.post("/v1/monitoring/silences", status_code=201)
async def create_silence_route(
    request: Request, body: SilenceCreateRequest,
) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    ctx_base = _build_ctx(request)
    if body.ends_at <= body.starts_at:
        raise _errors.AppError(
            "INVALID_WINDOW",
            "ends_at must be strictly after starts_at",
            400,
        )
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.create_silence(
            pool, conn, ctx,
            org_id=org_id,
            created_by=user_id,
            matcher=body.matcher.model_dump(exclude_none=True),
            starts_at=_naive(body.starts_at),
            ends_at=_naive(body.ends_at),
            reason=body.reason,
        )
    return _resp.success(SilenceResponse.from_row(row).model_dump(mode="json"))


@router.get("/v1/monitoring/silences", status_code=200)
async def list_silences_route(
    request: Request,
    active_only: bool = Query(default=True),
) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        rows = await _service.list_silences(
            conn, ctx, org_id=org_id, active_only=active_only,
        )
    items = [
        SilenceResponse.from_row(r).model_dump(mode="json") for r in rows
    ]
    return _resp.success({"items": items, "total": len(items)})


@router.delete(
    "/v1/monitoring/silences/{id}", status_code=204,
    response_class=Response,
)
async def delete_silence_route(request: Request, id: str) -> Response:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        ok = await _service.delete_silence(
            pool, conn, ctx, org_id=org_id, silence_id=id,
        )
    if not ok:
        raise _errors.NotFoundError(f"silence {id!r} not found")
    return Response(status_code=204)


# ── Alert event routes ────────────────────────────────────────────────

@router.get("/v1/monitoring/alerts", status_code=200)
async def list_alerts_route(
    request: Request,
    rule_id: str | None = Query(default=None),
    state: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        rows = await _service.list_alert_events(
            conn, ctx,
            org_id=org_id, rule_id=rule_id, state=state, severity=severity,
            since=_naive(since) if since else None,
            limit=limit,
        )
    items = [
        AlertEventResponse.from_row(r).model_dump(mode="json") for r in rows
    ]
    return _resp.success({"items": items, "total": len(items)})


@router.get("/v1/monitoring/alerts/{id}", status_code=200)
async def get_alert_route(
    request: Request,
    id: str,
    started_at: datetime = Query(...),
) -> dict:
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.get_alert_event(
            conn, ctx,
            org_id=org_id, event_id=id, started_at=_naive(started_at),
        )
    if row is None:
        raise _errors.NotFoundError(f"alert {id!r} not found")
    return _resp.success(AlertEventResponse.from_row(row).model_dump(mode="json"))


@router.post("/v1/monitoring/alerts/{id}/silence", status_code=201)
async def silence_alert_route(
    request: Request,
    id: str,
    body: SilenceCreateRequest,
    started_at: datetime = Query(...),
) -> dict:
    """Shortcut: silence an existing alert's fingerprint. Body matcher may be
    empty — when it is, matcher is filled from the alert's rule_id + labels.
    """
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    ctx_base = _build_ctx(request)
    if body.ends_at <= body.starts_at:
        raise _errors.AppError(
            "INVALID_WINDOW",
            "ends_at must be strictly after starts_at",
            400,
        )
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        alert = await _service.get_alert_event(
            conn, ctx,
            org_id=org_id, event_id=id, started_at=_naive(started_at),
        )
        if alert is None:
            raise _errors.NotFoundError(f"alert {id!r} not found")
        matcher = body.matcher.model_dump(exclude_none=True) or {
            "rule_id": str(alert["rule_id"]),
            "labels": alert.get("labels") or {},
        }
        row = await _service.create_silence(
            pool, conn, ctx,
            org_id=org_id,
            created_by=user_id,
            matcher=matcher,
            starts_at=_naive(body.starts_at),
            ends_at=_naive(body.ends_at),
            reason=body.reason,
        )
    return _resp.success(SilenceResponse.from_row(row).model_dump(mode="json"))

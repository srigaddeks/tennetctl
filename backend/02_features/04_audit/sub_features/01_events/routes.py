"""
audit.events — FastAPI routes (query path).

Four GETs — no mutations. The write path remains the audit.events.emit node,
called from other features' services.

HTTP reads emit an audit event (audit.events.queried) so there's a trail of
who inspected the audit log. Node-level reads (audit.events.query) skip this —
hot-path bypass matching the vault precedent.

v1 authz: session middleware sets request.state.user_id etc. Routes pass these
into NodeContext. Cross-org reads are allowed only for callers without a
session-bound org_id (i.e. system / admin callers pre-JWT); once a session has
an org_id, the filter is forced to match — cross-org queries return 403.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

import csv
import io

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_catalog: Any = import_module("backend.01_catalog")

_schemas: Any = import_module(
    "backend.02_features.04_audit.sub_features.01_events.schemas"
)
_service: Any = import_module(
    "backend.02_features.04_audit.sub_features.01_events.service"
)
_outbox_schemas: Any = import_module(
    "backend.02_features.04_audit.sub_features.03_outbox.schemas"
)
_outbox_service: Any = import_module(
    "backend.02_features.04_audit.sub_features.03_outbox.service"
)

AuditEventFilter = _schemas.AuditEventFilter
AuditEventListResponse = _schemas.AuditEventListResponse
AuditEventRow = _schemas.AuditEventRow
AuditEventStatsResponse = _schemas.AuditEventStatsResponse
AuditEventKeyRow = _schemas.AuditEventKeyRow
AuditEventKeyListResponse = _schemas.AuditEventKeyListResponse
FunnelRequest = _schemas.FunnelRequest
FunnelResponse = _schemas.FunnelResponse
FunnelStep = _schemas.FunnelStep
RetentionResponse = _schemas.RetentionResponse
RetentionCohort = _schemas.RetentionCohort
RetentionRetained = _schemas.RetentionRetained
AuditTailResponse = _outbox_schemas.AuditTailResponse
AuditEventRowSlim = _outbox_schemas.AuditEventRowSlim
AuditOutboxCursorResponse = _outbox_schemas.AuditOutboxCursorResponse


router = APIRouter(tags=["audit.events"])


def _naive_utc(dt: datetime | None) -> datetime | None:
    """Strip tz from a datetime — DB column is TIMESTAMP (tz-naive, app-UTC)."""
    if dt is None or dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _session_scope(request: Request) -> dict:
    """Read user_id / session_id / org_id / workspace_id from session middleware."""
    state = request.state
    return {
        "user_id": getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        "session_id": getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        "org_id": getattr(state, "org_id", None) or request.headers.get("x-org-id"),
        "workspace_id": getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
    }


def _build_ctx(request: Request, pool: Any, *, audit_category: str) -> Any:
    s = _session_scope(request)
    return _catalog_ctx.NodeContext(
        user_id=s["user_id"],
        session_id=s["session_id"],
        org_id=s["org_id"],
        workspace_id=s["workspace_id"],
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category=audit_category,
        pool=pool,
        extras={"pool": pool},
    )


def _enforce_org_authz(request: Request, filters: dict) -> None:
    """
    Cross-org guard. If the caller's session has an org_id bound, the filter
    org_id must match (or be absent, in which case we inject it). Callers
    without a session org_id (e.g. system/admin) can query any org.
    """
    s = _session_scope(request)
    session_org = s["org_id"]
    if session_org is None:
        return  # unscoped caller — allow any filter

    filter_org = filters.get("org_id")
    if filter_org is None:
        filters["org_id"] = session_org
        return

    if filter_org != session_org:
        raise HTTPException(
            status_code=403,
            detail={
                "ok": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "cross-org audit queries are not permitted for this session",
                },
            },
        )


_QUERIED_EVENT_KEY = "audit.events.queried"


async def _emit_queried(pool: Any, ctx: Any, *, route: str, filters: dict) -> None:
    """Emit audit.events.queried so the audit log records who inspected it."""
    try:
        await _catalog.run_node(
            pool,
            "audit.events.emit",
            ctx,
            {
                "event_key": _QUERIED_EVENT_KEY,
                "outcome": "success",
                "metadata": {"route": route, "filters": {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in filters.items() if v is not None}},
            },
        )
    except Exception:
        # Never fail the read because audit-of-reads failed. Log at INFO only.
        import logging
        logging.getLogger("tennetctl").info("audit.events.queried emit failed", exc_info=True)


@router.get("/v1/audit-events", status_code=200)
async def list_audit_events_route(
    request: Request,
    event_key: str | None = Query(default=None),
    category_code: str | None = Query(default=None),
    outcome: str | None = Query(default=None),
    actor_user_id: str | None = Query(default=None),
    actor_session_id: str | None = Query(default=None),
    org_id: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
    trace_id: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    q: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=1000),
    format: str | None = Query(default=None, pattern="^csv$"),
) -> Any:
    pool = request.app.state.pool

    filters: dict = {
        "event_key": event_key,
        "category_code": category_code,
        "outcome": outcome,
        "actor_user_id": actor_user_id,
        "actor_session_id": actor_session_id,
        "org_id": org_id,
        "workspace_id": workspace_id,
        "trace_id": trace_id,
        "since": _naive_utc(since),
        "until": _naive_utc(until),
        "q": q,
    }
    _enforce_org_authz(request, filters)

    # CSV export: fetch up to 10k rows (no cursor pagination), stream as CSV.
    if format == "csv":
        csv_limit = 10_000
        ctx_base = _build_ctx(request, pool, audit_category="system")
        async with pool.acquire() as conn:
            ctx = replace(ctx_base, conn=conn)
            try:
                items, _ = await _service.query(
                    conn, ctx, filters=filters, cursor=None, limit=csv_limit,
                )
            except ValueError as e:
                raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e

        _CSV_COLUMNS = [
            "id", "event_key", "event_label", "category_code", "category_label",
            "actor_user_id", "actor_session_id", "org_id", "workspace_id",
            "trace_id", "span_id", "outcome", "metadata", "created_at",
        ]

        def _generate() -> Any:
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=_CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            yield buf.getvalue()
            for row in items:
                buf = io.StringIO()
                writer = csv.DictWriter(buf, fieldnames=_CSV_COLUMNS, extrasaction="ignore")
                writer.writerow({k: (str(v) if v is not None else "") for k, v in row.items()})
                yield buf.getvalue()

        return StreamingResponse(
            _generate(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_events.csv"},
        )

    ctx_base = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        try:
            items, next_cursor = await _service.query(
                conn, ctx, filters=filters, cursor=cursor, limit=limit,
            )
        except ValueError as e:
            raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e

    # Fire-and-forget audit-of-reads in a fresh conn so it doesn't couple to the read tx.
    async with pool.acquire() as audit_conn:
        audit_ctx = replace(ctx_base, conn=audit_conn)
        await _emit_queried(pool, audit_ctx, route="list", filters=filters)

    data = [AuditEventRow(**row).model_dump() for row in items]
    return {"ok": True, "data": {"items": data, "next_cursor": next_cursor}}


@router.get("/v1/audit-events/stats", status_code=200)
async def stats_audit_events_route(
    request: Request,
    event_key: str | None = Query(default=None),
    category_code: str | None = Query(default=None),
    outcome: str | None = Query(default=None),
    actor_user_id: str | None = Query(default=None),
    actor_session_id: str | None = Query(default=None),
    org_id: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
    trace_id: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    q: str | None = Query(default=None),
    bucket: str = Query(default="hour", pattern="^(hour|day)$"),
) -> dict:
    pool = request.app.state.pool

    filters: dict = {
        "event_key": event_key,
        "category_code": category_code,
        "outcome": outcome,
        "actor_user_id": actor_user_id,
        "actor_session_id": actor_session_id,
        "org_id": org_id,
        "workspace_id": workspace_id,
        "trace_id": trace_id,
        "since": _naive_utc(since),
        "until": _naive_utc(until),
        "q": q,
    }
    _enforce_org_authz(request, filters)

    ctx_base = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        result = await _service.stats(conn, ctx, filters=filters, bucket=bucket)

    return _response.success(result)


@router.get("/v1/audit-event-keys", status_code=200)
async def list_audit_event_keys_route(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items, total = await _service.list_keys(conn)
    data = [AuditEventKeyRow(**row).model_dump() for row in items]
    return _response.success({"items": data, "total": total})


@router.post("/v1/audit-events/funnel", status_code=200)
async def funnel_route(request: Request, body: FunnelRequest) -> dict:
    """
    Funnel analysis: given an ordered list of event_key steps,
    return how many distinct actors completed each step.
    """
    pool = request.app.state.pool
    s = _session_scope(request)
    # Inject session org if caller didn't specify one.
    org_id = body.org_id or s["org_id"]
    async with pool.acquire() as conn:
        steps = await _service.funnel(
            conn,
            steps=body.steps,
            org_id=org_id,
            since=body.since,
            until=body.until,
        )
    return _response.success(FunnelResponse(steps=[FunnelStep(**s) for s in steps]).model_dump())


@router.get("/v1/audit-events/retention", status_code=200)
async def retention_route(
    request: Request,
    anchor: str = Query(..., description="Event key that defines cohort entry"),
    return_event: str = Query(..., description="Event key to track retention on"),
    org_id: str | None = Query(default=None),
    bucket: str = Query(default="week", pattern="^(day|week)$"),
    periods: int = Query(default=6, ge=1, le=52),
) -> dict:
    """
    Cohort retention: group actors by the week/day they first did `anchor`,
    then track how many returned with `return_event` in each subsequent period.
    """
    pool = request.app.state.pool
    s = _session_scope(request)
    effective_org = org_id or s["org_id"]
    async with pool.acquire() as conn:
        result = await _service.retention(
            conn,
            anchor=anchor,
            return_event=return_event,
            org_id=effective_org,
            bucket=bucket,
            periods=periods,
        )
    return _response.success(RetentionResponse(**result).model_dump())


@router.get("/v1/audit-events/outbox-cursor", status_code=200)
async def outbox_cursor_route(request: Request) -> dict:
    """Return the current max outbox id — use as `since_id` to start live tail from now."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        cursor = await _outbox_service.current_cursor(conn)
    return _response.success(AuditOutboxCursorResponse(last_outbox_id=cursor).model_dump())


@router.get("/v1/audit-events/tail", status_code=200)
async def tail_route(
    request: Request,
    since_id: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    org_id: str | None = Query(default=None),
) -> dict:
    """Poll the outbox for events newer than `since_id`. Returns items + new cursor."""
    pool = request.app.state.pool
    s = _session_scope(request)
    effective_org = org_id or s["org_id"]
    async with pool.acquire() as conn:
        rows = await _outbox_service.poll(conn, since_id=since_id, limit=limit, org_id=effective_org)
    last_id = rows[-1]["outbox_id"] if rows else since_id
    items = [AuditEventRowSlim(**r).model_dump() for r in rows]
    return _response.success(AuditTailResponse(items=items, last_outbox_id=last_id).model_dump())


@router.get("/v1/audit-events/{event_id}", status_code=200)
async def get_audit_event_route(request: Request, event_id: str) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.get(conn, ctx, event_id=event_id)
    if row is None:
        raise _errors.NotFoundError(f"audit event {event_id!r} not found.")

    # Cross-org check on the returned row
    s = _session_scope(request)
    if s["org_id"] is not None and row.get("org_id") is not None and row["org_id"] != s["org_id"]:
        raise HTTPException(
            status_code=403,
            detail={"ok": False, "error": {"code": "FORBIDDEN", "message": "cross-org audit access denied"}},
        )

    return _response.success(AuditEventRow(**row).model_dump())


# ── External emit endpoint ────────────────────────────────────────────────
# Added for SaaS apps (solsocial, etc.) that can't run catalog nodes in-process.
# The same validation + DB insert runs via the audit.events.emit node.

class _EmitAuditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_key: str
    outcome: Literal["success", "failure"] = "success"
    metadata: dict[str, Any] = Field(default_factory=dict)
    application_id: str | None = None
    org_id: str | None = None
    workspace_id: str | None = None
    actor_user_id: str | None = None  # end-user on whose behalf the app acted


@router.post("/v1/audit-events", status_code=201)
async def emit_audit_event_route(request: Request, body: _EmitAuditRequest) -> dict:
    """Emit an audit event from an external SaaS app.

    The caller's API key (or session) provides the service identity; the body
    carries end-user context on whose behalf the app is acting.
    """
    pool = request.app.state.pool
    s = _session_scope(request)
    ctx = _catalog_ctx.NodeContext(
        user_id=body.actor_user_id or s["user_id"],
        session_id=s["session_id"],
        org_id=body.org_id or s["org_id"],
        workspace_id=body.workspace_id or s["workspace_id"],
        application_id=body.application_id,
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="integration",
        pool=pool,
    )
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        result = await _catalog.run_node(
            pool, "audit.events.emit", ctx2,
            {
                "event_key": body.event_key,
                "outcome": body.outcome,
                "metadata": body.metadata,
            },
        )
    return _response.success(result)

"""
product_ops.events — FastAPI routes.

POST /v1/track       — anonymous batch ingest (no auth required; project_key in payload)
GET  /v1/product-events — admin read (session-scoped; cross-org guard)

Per CLAUDE.md simplicity: ONE ingest endpoint. event `kind` in the payload
routes via the ingest node's switch-on-kind logic. No /identify, /alias, /page.
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
_catalog: Any = import_module("backend.01_catalog")
_schemas: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.schemas"
)
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.service"
)

logger = logging.getLogger("tennetctl.product_ops")

router = APIRouter(tags=["product_ops.events"])


def _client_ip(request: Request) -> str | None:
    """X-Forwarded-For first hop, then request.client.host."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


def _build_anonymous_ctx(request: Request, pool: Any) -> Any:
    """
    Anonymous-first context. No user/session/org/workspace — those will be
    resolved from project_key inside the service. audit_category=setup so
    the audit triple-defense scope CHECK accepts the (anonymous) emit.

    extras carries pool + vault — vault.secrets.get demands ctx.extras['vault'].
    """
    extras: dict = {"pool": pool}
    vault = getattr(request.app.state, "vault", None)
    if vault is not None:
        extras["vault"] = vault
    return _catalog_ctx.NodeContext(
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="setup",
        extras=extras,
    )


# Session-scoped ctx builder will be added in 45-02 when identify() lands.


# ── POST /v1/track ──────────────────────────────────────────────────

@router.post("/v1/track", status_code=202)
async def track_route(request: Request) -> Any:
    """
    Anonymous batch ingest. DNT honored (drops events server-side too,
    not just client-side, for defense-in-depth).

    Returns 202 Accepted with envelope.
    """
    pool = request.app.state.pool

    raw = await request.json()
    try:
        batch = _schemas.TrackBatchIn(**raw)
    except Exception as e:
        raise _errors.AppError("BAD_REQUEST", str(e), status_code=400) from e

    # Honor DNT header even if SDK didn't set the body flag
    if request.headers.get("dnt") == "1":
        batch = batch.model_copy(update={"dnt": True})

    ctx = _build_anonymous_ctx(request, pool)
    client_ip = _client_ip(request)

    # Dispatch through the catalog (NCP v1). Node is tx=own — runner provides
    # its own conn in its own transaction.
    result = await _catalog.run_node(
        pool, "product_ops.events.ingest", ctx,
        {
            "project_key": batch.project_key,
            "events": [e.model_dump() for e in batch.events],
            "dnt": batch.dnt,
            "client_ip": client_ip,
        },
    )

    return _response.success(result)


# ── GET /v1/product-events (admin read) ─────────────────────────────

def _enforce_workspace_authz(request: Request, workspace_id: str | None) -> str:
    """
    Cross-workspace guard. If session has workspace_id, filter must match.
    Returns the resolved workspace_id (always non-None at exit).
    """
    state = request.state
    session_ws = (
        getattr(state, "workspace_id", None)
        or request.headers.get("x-workspace-id")
    )
    if session_ws is None and workspace_id is None:
        raise HTTPException(
            status_code=400,
            detail={"ok": False, "error": {
                "code": "BAD_REQUEST",
                "message": "workspace_id query param required (no session workspace).",
            }},
        )
    if session_ws is not None and workspace_id is not None and workspace_id != session_ws:
        raise HTTPException(
            status_code=403,
            detail={"ok": False, "error": {
                "code": "FORBIDDEN",
                "message": "cross-workspace product_ops queries are not permitted for this session",
            }},
        )
    resolved = workspace_id or session_ws
    assert resolved is not None  # the guard above ensures one of them is set
    return resolved


@router.get("/v1/product-events", status_code=200)
async def list_product_events_route(
    request: Request,
    workspace_id: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> Any:
    pool = request.app.state.pool
    resolved_ws = _enforce_workspace_authz(request, workspace_id)

    async with pool.acquire() as conn:
        result = await _service.list_events(
            conn, workspace_id=resolved_ws, limit=limit, cursor=cursor,
        )
    return _response.success(result)


# ── POST /v1/product-events/funnel ──────────────────────────────────

@router.post("/v1/product-events/funnel", status_code=200)
async def funnel_route(request: Request) -> Any:
    pool = request.app.state.pool
    raw = await request.json()
    steps = raw.get("steps") or []
    days = int(raw.get("days") or 30)
    workspace_id = raw.get("workspace_id")
    if not isinstance(steps, list) or not all(isinstance(s, str) for s in steps):
        raise _errors.AppError("BAD_REQUEST", "steps must be a list of event_name strings", status_code=400)
    if not steps:
        raise _errors.AppError("BAD_REQUEST", "steps cannot be empty", status_code=400)
    if len(steps) > 10:
        raise _errors.AppError("BAD_REQUEST", "max 10 funnel steps", status_code=400)

    resolved_ws = _enforce_workspace_authz(request, workspace_id)
    async with pool.acquire() as conn:
        from importlib import import_module as _im
        _repo: Any = _im(
            "backend.02_features.10_product_ops.sub_features.01_events.repository"
        )
        rows = await _repo.funnel_query(
            conn, workspace_id=resolved_ws, steps=steps, days=days,
        )
    return _response.success({"steps": rows, "days": days})


# ── GET /v1/product-events/retention ────────────────────────────────

@router.get("/v1/product-events/retention", status_code=200)
async def retention_route(
    request: Request,
    workspace_id: str | None = Query(default=None),
    cohort_event: str = Query(...),
    return_event: str = Query(...),
    weeks: int = Query(default=8, ge=2, le=52),
) -> Any:
    pool = request.app.state.pool
    resolved_ws = _enforce_workspace_authz(request, workspace_id)
    async with pool.acquire() as conn:
        from importlib import import_module as _im
        _repo: Any = _im(
            "backend.02_features.10_product_ops.sub_features.01_events.repository"
        )
        rows = await _repo.retention_matrix(
            conn, workspace_id=resolved_ws,
            cohort_event=cohort_event, return_event=return_event, weeks=weeks,
        )
    return _response.success({"cohorts": rows, "weeks": weeks})


# ── GET /v1/product-events/utm-aggregate ────────────────────────────

@router.get("/v1/product-events/utm-aggregate", status_code=200)
async def utm_aggregate_route(
    request: Request,
    workspace_id: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
) -> Any:
    pool = request.app.state.pool
    resolved_ws = _enforce_workspace_authz(request, workspace_id)
    async with pool.acquire() as conn:
        from importlib import import_module as _im
        _repo: Any = _im(
            "backend.02_features.10_product_ops.sub_features.01_events.repository"
        )
        rows = await _repo.utm_campaign_aggregate(
            conn, workspace_id=resolved_ws, days=days,
        )
    return _response.success({"rows": rows, "days": days})


# ── GET /v1/product-visitors/{id} ───────────────────────────────────

@router.get("/v1/product-visitors/{visitor_id}", status_code=200)
async def get_product_visitor_route(request: Request, visitor_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        from importlib import import_module as _im
        _repo: Any = _im(
            "backend.02_features.10_product_ops.sub_features.01_events.repository"
        )
        visitor = await _repo.get_visitor_by_id(conn, visitor_id)
        if visitor is None:
            raise _errors.AppError(
                "PRODUCT_OPS.VISITOR_NOT_FOUND",
                f"Visitor {visitor_id!r} not found.",
                status_code=404,
            )
        # Workspace authz
        state = request.state
        session_ws = (
            getattr(state, "workspace_id", None)
            or request.headers.get("x-workspace-id")
        )
        if session_ws and visitor["workspace_id"] != session_ws:
            raise HTTPException(
                status_code=403,
                detail={"ok": False, "error": {
                    "code": "FORBIDDEN",
                    "message": "visitor belongs to a different workspace",
                }},
            )

        # Attach last touch + aliases
        last = await _repo.get_last_touch_for_visitor(conn, visitor_id)
        aliases = await conn.fetch(
            'SELECT alias_anonymous_id, linked_at '
            'FROM "10_product_ops"."40_lnk_visitor_aliases" '
            'WHERE visitor_id = $1 ORDER BY linked_at DESC',
            visitor_id,
        )
    visitor["last_touch"] = dict(last) if last else None
    visitor["aliases"] = [dict(a) for a in aliases]
    return _response.success(visitor)

"""Routes for notify.send — POST /v1/notify/send transactional API."""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_errors: Any = import_module("backend.01_core.errors")
_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_middleware: Any = import_module("backend.01_core.middleware")
_schemas: Any = import_module("backend.02_features.06_notify.sub_features.11_send.schemas")
_service: Any = import_module("backend.02_features.06_notify.sub_features.11_send.service")

TransactionalSendRequest = _schemas.TransactionalSendRequest

router = APIRouter(tags=["notify.send"])


def _build_ctx(request: Request, pool: Any) -> Any:
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=getattr(state, "org_id", None) or request.headers.get("x-org-id"),
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", None) or _core_id.uuid7(),
        audit_category="setup",
        extras={"pool": pool},
    )


@router.post("/v1/notify/send", status_code=201)
async def send_transactional_route(request: Request, body: TransactionalSendRequest) -> dict:
    _middleware.require_scope(request, "notify:send")
    idempotency_key = request.headers.get("idempotency-key")

    # Resolve scheduled_at from either explicit time or relative delay.
    from datetime import datetime, timedelta, timezone
    scheduled_at = None
    if body.send_at is not None:
        # Normalize to naive UTC for DB TIMESTAMP (no tz) columns.
        s = body.send_at
        scheduled_at = s.astimezone(timezone.utc).replace(tzinfo=None) if s.tzinfo else s
    elif body.delay_seconds is not None:
        scheduled_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            seconds=body.delay_seconds
        )

    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        delivery_id, was_new = await _service.send_transactional(
            conn,
            pool,
            ctx2,
            org_id=body.org_id,
            template_key=body.template_key,
            recipient_user_id=body.recipient_user_id,
            channel_code=body.channel_code,
            variables=body.variables,
            deep_link=body.deep_link,
            idempotency_key=idempotency_key,
            scheduled_at=scheduled_at,
        )
    return _response.success({
        "delivery_id": delivery_id,
        "idempotent_replay": not was_new,
        "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
    })

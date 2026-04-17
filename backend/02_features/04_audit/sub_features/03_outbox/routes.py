"""
audit.outbox — FastAPI routes.

Two read-only endpoints that expose the durable outbox:

  GET /v1/audit-events/tail?since_id=<bigint>&limit=<int>&org_id=<uuid>
      Return up to `limit` events newer than `since_id` in the outbox.
      Consumers call this repeatedly, advancing `since_id` each time.
      Response: {ok, data: {items: [...], last_outbox_id: <int>}}

  GET /v1/audit-events/outbox-cursor
      Return the current max outbox id (use as initial since_id for live tail).
      Response: {ok, data: {last_outbox_id: <int>}}
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request

_response: Any = import_module("backend.01_core.response")
_schemas: Any = import_module(
    "backend.02_features.04_audit.sub_features.03_outbox.schemas"
)
_service: Any = import_module(
    "backend.02_features.04_audit.sub_features.03_outbox.service"
)

AuditTailResponse     = _schemas.AuditTailResponse
AuditEventRowSlim     = _schemas.AuditEventRowSlim
AuditOutboxCursorResponse = _schemas.AuditOutboxCursorResponse

router = APIRouter(tags=["audit.outbox"])


def _session_org(request: Request) -> str | None:
    state = request.state
    return getattr(state, "org_id", None) or request.headers.get("x-org-id")


@router.get("/v1/audit-events/tail", status_code=200)
async def tail_route(
    request: Request,
    since_id: int = Query(default=0, ge=0, description="Last outbox id seen; 0 = start of tail"),
    limit: int = Query(default=50, ge=1, le=500),
    org_id: str | None = Query(default=None),
) -> dict:
    pool = request.app.state.pool
    # Apply session org if no explicit org_id provided.
    effective_org = org_id or _session_org(request)
    async with pool.acquire() as conn:
        rows = await _service.poll(conn, since_id=since_id, limit=limit, org_id=effective_org)

    last_id = rows[-1]["outbox_id"] if rows else since_id
    items = [AuditEventRowSlim(**r).model_dump() for r in rows]
    return _response.success(
        AuditTailResponse(items=items, last_outbox_id=last_id).model_dump()
    )


@router.get("/v1/audit-events/outbox-cursor", status_code=200)
async def outbox_cursor_route(request: Request) -> dict:
    """Return the current max outbox id — use as `since_id` to start live tail from now."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        cursor = await _service.current_cursor(conn)
    return _response.success(AuditOutboxCursorResponse(last_outbox_id=cursor).model_dump())

"""
product_ops.track — FastAPI routes.

Public ingestion: POST /v1/track  (no auth required, accepts anonymous traffic)
Read API:         GET  /v1/product-ops/events
                  GET  /v1/product-ops/counts
                  GET  /v1/product-ops/event-keys
"""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Literal

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, ConfigDict, Field

_response: Any = import_module("backend.01_core.response")
_service: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_track.service"
)


class TrackEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: str = Field(..., min_length=1, max_length=200)
    distinct_id: str = Field(..., min_length=1, max_length=200)
    session_id: str | None = Field(default=None, max_length=200)
    source: Literal["web", "mobile", "server", "backend", "other"] = "web"
    url: str | None = Field(default=None, max_length=2000)
    properties: dict[str, Any] = Field(default_factory=dict)
    org_id: str | None = None
    workspace_id: str | None = None
    actor_user_id: str | None = None


class TrackEventResponse(BaseModel):
    id: str
    created_at: datetime


class ProductEventRow(BaseModel):
    id: str
    org_id: str
    workspace_id: str | None
    actor_user_id: str | None
    distinct_id: str
    event_name: str
    session_id: str | None
    source: str
    url: str | None
    user_agent: str | None
    ip_addr: str | None
    properties: dict[str, Any]
    created_at: datetime


class TopEventRow(BaseModel):
    event_name: str
    count: int


class CountsResponse(BaseModel):
    events_today: int
    events_24h: int
    dau: int
    distinct_ids_24h: int
    top_events_24h: list[TopEventRow]

router = APIRouter(tags=["product_ops"])


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def _session_org(request: Request) -> str | None:
    return (
        getattr(request.state, "org_id", None)
        or request.headers.get("x-org-id")
    )


def _naive_utc(dt: datetime | None) -> datetime | None:
    if dt is None or dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


@router.post("/v1/track", status_code=201)
async def track_event_route(
    request: Request, body: TrackEventRequest,
) -> dict:
    pool = request.app.state.pool
    user_agent = request.headers.get("user-agent")
    ip_addr = _client_ip(request)
    org_id = body.org_id or _session_org(request) or _service.ANON_ORG_ID
    actor_user_id = body.actor_user_id or getattr(request.state, "user_id", None)
    workspace_id = body.workspace_id or getattr(request.state, "workspace_id", None)
    async with pool.acquire() as conn:
        result = await _service.track(
            conn,
            event=body.event,
            distinct_id=body.distinct_id,
            org_id=org_id,
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            session_id=body.session_id,
            source=body.source,
            url=body.url,
            user_agent=user_agent,
            ip_addr=ip_addr,
            properties=body.properties,
        )
    return _response.success(TrackEventResponse(**result).model_dump())


@router.get("/v1/product-ops/events", status_code=200)
async def list_events_route(
    request: Request,
    event_name: str | None = Query(default=None),
    distinct_id: str | None = Query(default=None),
    actor_user_id: str | None = Query(default=None),
    source: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    org_id: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> dict:
    pool = request.app.state.pool
    effective_org = org_id or _session_org(request) or _service.ANON_ORG_ID
    async with pool.acquire() as conn:
        items, next_cursor = await _service.list_events(
            conn,
            org_id=effective_org,
            event_name=event_name,
            distinct_id=distinct_id,
            actor_user_id=actor_user_id,
            source=source,
            since=_naive_utc(since),
            until=_naive_utc(until),
            cursor=cursor,
            limit=limit,
        )
    data = [ProductEventRow(**r).model_dump() for r in items]
    return _response.success({"items": data, "next_cursor": next_cursor})


@router.get("/v1/product-ops/counts", status_code=200)
async def counts_route(
    request: Request, org_id: str | None = Query(default=None),
) -> dict:
    pool = request.app.state.pool
    effective_org = org_id or _session_org(request) or _service.ANON_ORG_ID
    async with pool.acquire() as conn:
        result = await _service.counts(conn, org_id=effective_org)
    return _response.success(CountsResponse(**result).model_dump())


@router.get("/v1/product-ops/event-keys", status_code=200)
async def event_keys_route(
    request: Request, org_id: str | None = Query(default=None),
) -> dict:
    pool = request.app.state.pool
    effective_org = org_id or _session_org(request) or _service.ANON_ORG_ID
    async with pool.acquire() as conn:
        keys = await _service.list_event_keys(conn, org_id=effective_org)
    return _response.success({"items": keys, "total": len(keys)})

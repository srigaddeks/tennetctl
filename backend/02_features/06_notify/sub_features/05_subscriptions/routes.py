"""Routes for notify.subscriptions — CRUD at /v1/notify/subscriptions."""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_errors: Any = import_module("backend.01_core.errors")
_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_schemas: Any = import_module(
    "backend.02_features.06_notify.sub_features.05_subscriptions.schemas"
)
_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.05_subscriptions.service"
)

SubscriptionCreate = _schemas.SubscriptionCreate
SubscriptionUpdate = _schemas.SubscriptionUpdate
SubscriptionRow = _schemas.SubscriptionRow

router = APIRouter(tags=["notify.subscriptions"])


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


@router.get("/v1/notify/subscriptions", status_code=200)
async def list_subscriptions_route(request: Request) -> dict:
    org_id = request.query_params.get("org_id") or request.headers.get("x-org-id")
    if not org_id:
        raise _errors.ValidationError("org_id query param is required")
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items = await _service.list_subscriptions(conn, org_id=org_id)
    data = [SubscriptionRow(**r).model_dump() for r in items]
    return _response.success({"items": data, "total": len(data)})


@router.post("/v1/notify/subscriptions", status_code=201)
async def create_subscription_route(request: Request, body: SubscriptionCreate) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        row = await _service.create_subscription(
            conn, pool, ctx2, data=body.model_dump()
        )
    return _response.success(SubscriptionRow(**row).model_dump())


@router.get("/v1/notify/subscriptions/{sub_id}", status_code=200)
async def get_subscription_route(request: Request, sub_id: str) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_subscription(conn, sub_id=sub_id)
    if row is None:
        raise _errors.NotFoundError(f"subscription {sub_id!r} not found")
    return _response.success(SubscriptionRow(**row).model_dump())


@router.patch("/v1/notify/subscriptions/{sub_id}", status_code=200)
async def update_subscription_route(
    request: Request, sub_id: str, body: SubscriptionUpdate
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        row = await _service.update_subscription(
            conn, pool, ctx2, sub_id=sub_id,
            data=body.model_dump(exclude_none=True),
        )
    if row is None:
        raise _errors.NotFoundError(f"subscription {sub_id!r} not found")
    return _response.success(SubscriptionRow(**row).model_dump())


@router.delete("/v1/notify/subscriptions/{sub_id}", status_code=204)
async def delete_subscription_route(request: Request, sub_id: str) -> None:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        deleted = await _service.delete_subscription(conn, pool, ctx2, sub_id=sub_id)
    if not deleted:
        raise _errors.NotFoundError(f"subscription {sub_id!r} not found")

"""Routes for notify.deliveries at /v1/notify/deliveries."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

_errors: Any = import_module("backend.01_core.errors")
_response: Any = import_module("backend.01_core.response")
_schemas: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.schemas"
)
_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.service"
)

DeliveryRow = _schemas.DeliveryRow

router = APIRouter(tags=["notify.deliveries"])


class DeliveryPatchBody(BaseModel):
    status: str  # "opened" is the only supported value for now (mark-read)


@router.get("/v1/notify/unread-count", status_code=200)
async def unread_count_route(request: Request) -> dict:
    """Server-computed unread notification count for the current user.

    Unread = status NOT IN (opened, clicked, failed, unsubscribed, bounced).
    Scoped to the recipient_user_id query param OR the session user.
    """
    user_id = request.query_params.get("recipient_user_id") or getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    org_id = request.query_params.get("org_id") or getattr(request.state, "org_id", None) or request.headers.get("x-org-id")
    if not org_id:
        raise _errors.ValidationError("org_id is required")

    pool = request.app.state.pool
    async with pool.acquire() as conn:
        count = await _service.unread_count(
            conn, org_id=org_id, recipient_user_id=user_id,
        )
    return _response.success({"count": count})


@router.get("/v1/notify/deliveries", status_code=200)
async def list_deliveries_route(request: Request) -> dict:
    org_id = request.query_params.get("org_id") or request.headers.get("x-org-id")
    if not org_id:
        raise _errors.ValidationError("org_id query param is required")
    status_code = request.query_params.get("status")
    channel_code = request.query_params.get("channel")
    recipient_user_id = request.query_params.get("recipient_user_id")
    try:
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
    except ValueError:
        raise _errors.ValidationError("limit and offset must be integers")

    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items = await _service.list_deliveries(
            conn,
            org_id=org_id,
            status_code=status_code,
            channel_code=channel_code,
            recipient_user_id=recipient_user_id,
            limit=limit,
            offset=offset,
        )
    data = [DeliveryRow(**r).model_dump() for r in items]
    return _response.success({"items": data, "total": len(data)})


@router.get("/v1/notify/deliveries/{delivery_id}", status_code=200)
async def get_delivery_route(request: Request, delivery_id: str) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_delivery(conn, delivery_id=delivery_id)
    if row is None:
        raise _errors.NotFoundError(f"delivery {delivery_id!r} not found")
    return _response.success(DeliveryRow(**row).model_dump())


@router.patch("/v1/notify/deliveries/{delivery_id}", status_code=200)
async def patch_delivery_route(
    delivery_id: str, body: DeliveryPatchBody, request: Request
) -> dict:
    """Mark a delivery as read, across any channel.

    Only `status: "opened"` is supported. Caller must be the recipient.
    Requires authentication.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)

    if body.status != "opened":
        raise _errors.ValidationError(
            f"unsupported status transition {body.status!r}; only 'opened' is supported"
        )

    pool = request.app.state.pool
    async with pool.acquire() as conn:
        updated = await _service.mark_read(
            conn, delivery_id=delivery_id, user_id=user_id
        )
    return _response.success(DeliveryRow(**updated).model_dump())

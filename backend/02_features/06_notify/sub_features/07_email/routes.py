"""
Routes for notify.email:
  GET  /v1/notify/email/track/o/{token}    — open tracking (1px GIF + delivery event)
  GET  /v1/notify/email/track/c/{token}    — click tracking (redirect + delivery event)
  POST /v1/notify/email/webhooks/bounce    — bounce notification from SMTP provider
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytracking
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel

_resp: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_del_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.repository"
)

router = APIRouter(tags=["notify.email"])

# 1-pixel transparent GIF (43 bytes)
_TRANSPARENT_GIF = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x21,
    0xf9, 0x04, 0x01, 0x00, 0x00, 0x00, 0x00, 0x2c, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3b,
])

_PYTRACK_CONFIG = pytracking.Configuration()


class BouncePayload(BaseModel):
    delivery_id: str
    reason: str | None = None


@router.get("/v1/notify/email/track/o/{token}", response_class=Response)
async def open_tracking_route(token: str, request: Request) -> Response:
    """Record an email open and return a 1px transparent GIF."""
    try:
        result = pytracking.get_open_tracking_result(token, configuration=_PYTRACK_CONFIG)
        delivery_id = result.metadata.get("delivery_id") if result.metadata else None
    except Exception:
        delivery_id = None

    if delivery_id:
        try:
            async with request.app.state.pool.acquire() as conn:
                event_id = _core_id.uuid7()
                await _del_repo.create_delivery_event(
                    conn,
                    event_id=event_id,
                    delivery_id=delivery_id,
                    event_type="open",
                    metadata={},
                )
                delivery = await _del_repo.get_delivery(conn, delivery_id)
                # Only advance status if currently sent/delivered
                if delivery and delivery.get("status_id") in (3, 4):
                    await _del_repo.update_delivery_status(
                        conn, delivery_id=delivery_id, status_id=5
                    )
        except Exception:
            pass  # tracking must never break email receipt

    return Response(content=_TRANSPARENT_GIF, media_type="image/gif")


@router.get("/v1/notify/email/track/c/{token}", response_class=RedirectResponse)
async def click_tracking_route(token: str, request: Request) -> RedirectResponse:
    """Record a link click and redirect to the original URL."""
    fallback_url = "/"
    try:
        result = pytracking.get_click_tracking_result(token, configuration=_PYTRACK_CONFIG)
        tracked_url = result.tracked_url or fallback_url
        delivery_id = result.metadata.get("delivery_id") if result.metadata else None
    except Exception:
        return RedirectResponse(url=fallback_url, status_code=302)

    if delivery_id:
        try:
            async with request.app.state.pool.acquire() as conn:
                event_id = _core_id.uuid7()
                await _del_repo.create_delivery_event(
                    conn,
                    event_id=event_id,
                    delivery_id=delivery_id,
                    event_type="click",
                    metadata={"url": tracked_url},
                )
                delivery = await _del_repo.get_delivery(conn, delivery_id)
                # Advance to clicked if currently sent/delivered/opened
                if delivery and delivery.get("status_id") in (3, 4, 5):
                    await _del_repo.update_delivery_status(
                        conn, delivery_id=delivery_id, status_id=6
                    )
        except Exception:
            pass

    return RedirectResponse(url=tracked_url, status_code=302)


@router.post("/v1/notify/email/webhooks/bounce")
async def bounce_webhook_route(payload: BouncePayload, request: Request) -> dict:
    """Record a bounce received from an SMTP provider."""
    async with request.app.state.pool.acquire() as conn:
        delivery = await _del_repo.get_delivery(conn, payload.delivery_id)
        if delivery is None:
            raise _errors.AppError(
                "NOT_FOUND", f"delivery {payload.delivery_id!r} not found", 404
            )

        event_id = _core_id.uuid7()
        await _del_repo.create_delivery_event(
            conn,
            event_id=event_id,
            delivery_id=payload.delivery_id,
            event_type="bounce",
            metadata={"reason": payload.reason or ""},
        )
        updated = await _del_repo.update_delivery_status(
            conn,
            delivery_id=payload.delivery_id,
            status_id=7,  # bounced
            failure_reason=payload.reason,
        )
    return _resp.success({"delivery": updated})

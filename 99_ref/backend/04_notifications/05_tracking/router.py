from __future__ import annotations

import re
from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request
from fastapi.responses import RedirectResponse, Response

from .dependencies import get_tracking_service
from .service import TrackingService

_telemetry_module = import_module("backend.01_core.telemetry")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter

router = InstrumentedAPIRouter(prefix="/api/v1/notifications/track", tags=["notification-tracking"])

GIF_PIXEL = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
    b'\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
    b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
)

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)

_PIXEL_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "Thu, 01 Jan 1970 00:00:00 GMT",
}


@router.get("/open/{notification_id}")
async def track_open(
    notification_id: str,
    request: Request,
    service: Annotated[TrackingService, Depends(get_tracking_service)],
) -> Response:
    # Quick UUID validation — avoid DB hit for garbage IDs
    if not _UUID_RE.match(notification_id):
        return Response(content=GIF_PIXEL, media_type="image/gif", headers=_PIXEL_HEADERS)
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    await service.record_open(notification_id, user_agent, ip_address)
    return Response(content=GIF_PIXEL, media_type="image/gif", headers=_PIXEL_HEADERS)


@router.get("/click/{notification_id}")
async def track_click(
    notification_id: str,
    url: Annotated[str, Query(min_length=1)],
    request: Request,
    service: Annotated[TrackingService, Depends(get_tracking_service)],
) -> RedirectResponse:
    # UUID validation — still redirect even if invalid ID
    if _UUID_RE.match(notification_id):
        user_agent = request.headers.get("user-agent")
        ip_address = request.client.host if request.client else None
        await service.record_click(notification_id, url, user_agent, ip_address)
    return RedirectResponse(url=url)

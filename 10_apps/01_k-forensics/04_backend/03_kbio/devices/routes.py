"""kbio devices routes.

Internal endpoints for the device registry.
All endpoints require the X-Internal-Service-Token header.
"""
from __future__ import annotations

import importlib

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

_db = importlib.import_module("01_core.db")
_resp = importlib.import_module("01_core.response")
_errors = importlib.import_module("01_core.errors")
_config = importlib.import_module("01_core.config")

from .schemas import PatchDeviceRequest
from .service import get_device, list_devices, update_device_trust

router = APIRouter(prefix="/v1/internal", tags=["kbio-devices"])


def _validate_service_token(request: Request) -> None:
    """Raise 401 AppError if X-Internal-Service-Token is missing or wrong."""
    settings = _config.get_settings()
    token = request.headers.get("X-Internal-Service-Token", "")
    if not token or token != settings.kbio_internal_service_token:
        raise _errors.AppError(
            "UNAUTHORIZED",
            "Missing or invalid X-Internal-Service-Token.",
            401,
        )


@router.get(
    "/devices/{user_hash}",
    summary="List devices for a user",
)
async def list_devices_endpoint(
    user_hash: str,
    request: Request,
    limit: int = Query(default=20, ge=1, le=200, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
) -> dict:
    """Return a paginated list of devices linked to the given user_hash.

    Ordered by first_seen_at descending.

    Headers:
        X-Internal-Service-Token: shared service secret

    Query params:
        limit (int, 1–200): page size, default 20
        offset (int, >= 0): page offset, default 0

    Returns:
        200: {"ok": true, "data": {"items": [...], "total": N, "limit": N, "offset": N}}
        401: missing/invalid token
    """
    _validate_service_token(request)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            result = await list_devices(conn, user_hash, limit=limit, offset=offset)
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_list_response(
        [d.model_dump() for d in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.patch(
    "/devices/{device_id}",
    summary="Trust or untrust a device",
)
async def patch_device_endpoint(
    device_id: str,
    body: PatchDeviceRequest,
    request: Request,
) -> dict:
    """Update the trust status of a device.

    The actor_id is taken from the X-Actor-ID header if provided,
    otherwise defaults to the string literal 'service'.

    Headers:
        X-Internal-Service-Token: shared service secret
        X-Actor-ID (optional): who is making the change

    Body:
        trusted: bool
        reason: str

    Returns:
        200: {"ok": true, "data": DeviceData}
        401: missing/invalid token
        404: device not found
        500: unexpected failure
    """
    _validate_service_token(request)

    actor_id = request.headers.get("X-Actor-ID", "service")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            result = await update_device_trust(
                conn,
                device_id,
                trusted=body.trusted,
                reason=body.reason,
                actor_id=actor_id,
            )
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response(result.model_dump())

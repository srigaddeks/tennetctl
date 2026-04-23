"""social_publisher.capture — routes for POST/GET /v1/social/captures."""
from __future__ import annotations

import datetime as dt
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_schemas: Any = import_module(
    "backend.02_features.07_social_publisher.capture_schemas"
)
_svc: Any = import_module(
    "backend.02_features.07_social_publisher.capture_service"
)

router = APIRouter()


def _require_auth(request: Request) -> dict:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.UnauthorizedError("authentication required")
    return {
        "user_id": user_id,
        "id": getattr(request.state, "session_id", None) or "",
        "org_id": getattr(request.state, "org_id", None) or "",
        "workspace_id": getattr(request.state, "workspace_id", None) or "",
    }


@router.post("/v1/social/captures")
async def ingest_captures(request: Request):
    session = _require_auth(request)
    raw = await request.json()
    body = _schemas.CaptureBatchIn.model_validate(raw)
    pool = request.app.state.pool

    async with pool.acquire() as conn:
        result = await _svc.ingest_batch(
            conn,
            user_id=session["user_id"],
            org_id=session.get("org_id") or "",
            session_id=session["id"],
            captures_in=[c.model_dump() for c in body.captures],
        )

    return _response.success(_schemas.CaptureBatchOut(**result).model_dump())


@router.get("/v1/social/captures")
async def list_captures(
    request: Request,
    platform: str | None = Query(None),
    type: str | None = Query(None),
    org_id: str | None = Query(None),
    from_dt: dt.datetime | None = Query(None),
    to_dt: dt.datetime | None = Query(None),
    is_own: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    session = _require_auth(request)
    pool = request.app.state.pool

    async with pool.acquire() as conn:
        result = await _svc.list_captures(
            conn,
            user_id=session["user_id"],
            org_id=org_id,
            platform=platform,
            capture_type=type,
            from_dt=from_dt,
            to_dt=to_dt,
            is_own=is_own,
            limit=limit,
            offset=offset,
        )

    items = [_schemas.CaptureOut(**item).model_dump() for item in result["items"]]
    return _response.success(
        _schemas.CaptureListOut(
            items=items,
            total=result["total"],
            limit=limit,
            offset=offset,
        ).model_dump()
    )

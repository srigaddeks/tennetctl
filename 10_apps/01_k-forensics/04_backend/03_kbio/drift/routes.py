"""kbio drift routes.

Internal endpoints consumed by kprotect to query live session drift state.
All endpoints require the X-Internal-Service-Token header.
"""
from __future__ import annotations

import importlib

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

_db = importlib.import_module("01_core.db")
_resp = importlib.import_module("01_core.response")
_errors = importlib.import_module("01_core.errors")
_auth = importlib.import_module("01_core.api_key_auth")

from .service import get_drift_state, get_drift_trend

router = APIRouter(prefix="/v1/internal", tags=["kbio-drift"])


@router.get(
    "/drift/{session_id}",
    summary="Get current drift state for a session",
)
async def get_drift(
    session_id: str,
    request: Request,
) -> dict:
    """Return the current drift state for the given SDK session ID.

    Fetched from Valkey cache first, falling back to the DB view.

    Headers:
        X-Internal-Service-Token: shared service secret

    Returns:
        200: {"ok": true, "data": DriftState}
        401: missing/invalid token
        404: session not found
    """
    await _auth.validate_api_key(request)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            state = await get_drift_state(conn, session_id)
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response(state.model_dump())


@router.get(
    "/drift/{session_id}/trend",
    summary="Get recent score events (drift trend) for a session",
)
async def get_drift_trend_endpoint(
    session_id: str,
    request: Request,
    limit: int = Query(default=20, ge=1, le=100, description="Max score events to return"),
) -> dict:
    """Return the most recent score events for the given SDK session ID.

    Ordered newest-first. Useful for graphing drift over time.

    Headers:
        X-Internal-Service-Token: shared service secret

    Returns:
        200: {"ok": true, "data": {"events": [...], "session_id": "..."}}
        401: missing/invalid token
        404: session not found
    """
    await _auth.validate_api_key(request)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            events = await get_drift_trend(conn, session_id, limit=limit)
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response({"session_id": session_id, "events": events})

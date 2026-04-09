"""kbio profile routes.

Internal endpoints for user behavioral profile management.
All endpoints require the X-Internal-Service-Token header.
"""
from __future__ import annotations

import importlib

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

_db = importlib.import_module("01_core.db")
_resp = importlib.import_module("01_core.response")
_errors = importlib.import_module("01_core.errors")
_config = importlib.import_module("01_core.config")

from .service import (
    get_profile_summary,
    create_profile,
    update_profile_from_genuine_session,
)

router = APIRouter(prefix="/v1/internal", tags=["kbio-profile"])


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


class CreateProfileRequest(BaseModel):
    actor_id: str


class UpdateProfileRequest(BaseModel):
    actor_id: str
    features: dict[str, float]
    drift_score: float = 0.0  # Caller-provided score; service enforces < 0.3 threshold.


@router.get(
    "/profile/{user_hash}",
    summary="Get behavioral profile for a user",
)
async def get_profile_endpoint(
    user_hash: str,
    request: Request,
) -> dict:
    """Return the behavioral profile summary for the given user_hash.

    Fetched from Valkey cache first, falling back to v_user_profiles.

    Headers:
        X-Internal-Service-Token: shared service secret

    Returns:
        200: {"ok": true, "data": ProfileSummary}
        401: missing/invalid token
        404: profile not found
    """
    _validate_service_token(request)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            summary = await get_profile_summary(conn, user_hash)
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response(summary.model_dump())


@router.post(
    "/profile",
    status_code=201,
    summary="Create a new behavioral profile",
)
async def create_profile_endpoint(
    body: CreateProfileRequest,
    request: Request,
) -> dict:
    """Create a new behavioral profile for the given user_hash.

    If a profile already exists the call is idempotent (upsert).

    Headers:
        X-Internal-Service-Token: shared service secret

    Body:
        user_hash: str
        actor_id: str

    Returns:
        201: {"ok": true, "data": ProfileSummary}
        401: missing/invalid token
        500: unexpected DB failure
    """
    _validate_service_token(request)

    # user_hash passed as a query param to keep POST body minimal.
    user_hash = request.query_params.get("user_hash", "")
    if not user_hash:
        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "error": {"code": "VALIDATION_ERROR", "message": "user_hash query param required."},
            },
        )

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            summary = await create_profile(conn, user_hash=user_hash, actor_id=body.actor_id)
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response(summary.model_dump())


@router.patch(
    "/profile/{user_hash}/features",
    summary="Update profile features from a genuine session",
)
async def update_profile_features(
    user_hash: str,
    body: UpdateProfileRequest,
    request: Request,
) -> dict:
    """Apply an EMA (alpha=0.1) update to profile feature attributes.

    Only applied when drift_score < 0.3 (genuine session). The caller
    is responsible for gating this endpoint on session genuineness, but the
    service enforces the threshold as a second line of defense.

    Headers:
        X-Internal-Service-Token: shared service secret

    Returns:
        200: {"ok": true, "data": {"user_hash": "...", "updated": true}}
        401: missing/invalid token
        422: drift_score >= 0.3 or empty features
    """
    _validate_service_token(request)

    if body.drift_score >= 0.3:
        return JSONResponse(
            status_code=422,
            content={
                "ok": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"drift_score {body.drift_score:.3f} >= 0.3 — session not genuine.",
                },
            },
        )

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            await update_profile_from_genuine_session(
                conn,
                user_hash=user_hash,
                features=body.features,
                actor_id=body.actor_id,
            )
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response({"user_hash": user_hash, "updated": True})

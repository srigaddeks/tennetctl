"""kbio challenge routes.

Internal endpoints for KP-Challenge behavioral TOTP.
All endpoints require the X-Internal-Service-Token header.
"""
from __future__ import annotations

import importlib

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

_db = importlib.import_module("01_core.db")
_resp = importlib.import_module("01_core.response")
_errors = importlib.import_module("01_core.errors")
_auth = importlib.import_module("01_core.api_key_auth")

from .schemas import ChallengeGenerateRequest, ChallengeVerifyRequest
from .service import generate_challenge, verify_challenge

router = APIRouter(prefix="/v1/internal", tags=["kbio-challenge"])


@router.post(
    "/challenge/generate",
    status_code=201,
    summary="Generate a KP-Challenge behavioral TOTP prompt",
)
async def generate_challenge_endpoint(
    body: ChallengeGenerateRequest,
    request: Request,
) -> dict:
    """Generate a new KP-Challenge phrase for the user to type.

    The caller receives a phrase, a challenge_id, and an expiry timestamp.
    The SDK should capture keystroke telemetry while the user types the phrase
    and submit it via the verify endpoint.

    Headers:
        X-Internal-Service-Token: shared service secret

    Body:
        session_id: str
        user_hash: str
        purpose: str

    Returns:
        201: {"ok": true, "data": ChallengeGenerateResponse}
        401: missing/invalid token
        500: unexpected failure
    """
    await _auth.validate_api_key(request)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            result = await generate_challenge(
                conn,
                session_id=body.session_id,
                user_hash=body.user_hash,
                purpose=body.purpose,
            )
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response(result.model_dump())


@router.post(
    "/challenge/verify",
    summary="Verify a KP-Challenge behavioral response",
)
async def verify_challenge_endpoint(
    body: ChallengeVerifyRequest,
    request: Request,
) -> dict:
    """Verify the behavioral telemetry submitted for a KP-Challenge.

    Performs expiry/replay checks, anti-bot plausibility validation, and
    scores behavioral drift against the enrolled user profile.

    Headers:
        X-Internal-Service-Token: shared service secret

    Body:
        challenge_id: str
        session_id: str
        user_hash: str
        response_batch: dict — keystroke telemetry from the SDK

    Returns:
        200: {"ok": true, "data": ChallengeVerifyResponse}
        401: missing/invalid token
        404: challenge not found
        409: challenge already used
        410: challenge expired
        422: anti-bot check failed / validation error
    """
    await _auth.validate_api_key(request)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            result = await verify_challenge(
                conn,
                challenge_id=body.challenge_id,
                session_id=body.session_id,
                user_hash=body.user_hash,
                response_batch=body.response_batch,
            )
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response(result.model_dump())

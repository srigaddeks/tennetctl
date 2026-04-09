"""kbio ingest routes.

POST /v1/internal/ingest — Receive behavioral batch (called by kprotect)
POST /v1/internal/score  — On-demand composite score (called by kprotect)

Both require X-Internal-Service-Token header for service-to-service auth.
"""

from __future__ import annotations

import importlib
import gzip

from fastapi import APIRouter, Request

_service = importlib.import_module("03_kbio.ingest.service")
_schemas = importlib.import_module("03_kbio.ingest.schemas")
_errors = importlib.import_module("01_core.errors")
_config = importlib.import_module("01_core.config")
_resp = importlib.import_module("01_core.response")

router = APIRouter(prefix="/v1/internal", tags=["kbio-ingest"])


def _validate_service_token(request: Request) -> None:
    """Validate internal service-to-service auth token."""
    settings = _config.get_settings()
    token = request.headers.get("X-Internal-Service-Token", "")
    if token != settings.kbio_internal_service_token:
        raise _errors.AppError("UNAUTHORIZED", "Invalid service token.", 401)


@router.post("/ingest")
async def ingest_batch(request: Request) -> dict:
    """Receive a behavioral batch and return drift scores."""
    _validate_service_token(request)

    # Handle gzip-compressed bodies
    body = await request.body()
    if request.headers.get("content-encoding") == "gzip":
        body = gzip.decompress(body)

    import json
    batch = json.loads(body)

    headers = {
        "X-KP-Session": request.headers.get("X-KP-Session", ""),
        "X-KP-Device": request.headers.get("X-KP-Device", ""),
        "X-KP-SDK-Version": request.headers.get("X-KP-SDK-Version", ""),
    }

    result = await _service.ingest_batch(batch, headers=headers)
    return _resp.success_response(result)


@router.post("/score")
async def on_demand_score(request: Request) -> dict:
    """Return a composite risk score for a session (called by kprotect)."""
    _validate_service_token(request)

    body = await request.json()
    score_req = _schemas.ScoreRequest(**body)

    # For V1, delegate to the ingest service's profile/session lookup
    # and return cached scores
    import json as _json
    _valkey_mod = importlib.import_module("01_core.valkey")
    valkey = _valkey_mod.get_client()

    session_key = f"kbio:session:{score_req.session_id}"
    session_raw = await valkey.get(session_key)

    if not session_raw:
        raise _errors.AppError("SESSION_NOT_FOUND", f"Session '{score_req.session_id}' not found.", 404)

    session_state = _json.loads(session_raw)

    return _resp.success_response({
        "session_id": score_req.session_id,
        "user_hash": score_req.user_hash,
        "behavioral_drift": session_state.get("current_drift_score", -1.0),
        "device_drift": -1.0,
        "network_drift": -1.0,
        "bot_score": session_state.get("bot_score", 0.0),
        "composite_score": session_state.get("current_drift_score", -1.0),
        "confidence": 0.5,
        "action": "allow",
        "baseline_quality": session_state.get("baseline_quality", "insufficient"),
        "auth_state": {
            "session_trust": session_state.get("trust_level", "trusted"),
            "device_known": True,
            "baseline_quality": session_state.get("baseline_quality", "insufficient"),
        },
    })

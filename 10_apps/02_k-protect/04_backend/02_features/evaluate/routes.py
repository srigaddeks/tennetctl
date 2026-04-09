"""kprotect evaluate routes.

POST /v1/evaluate — Main SDK-facing endpoint
POST /v1/challenge/generate — Forward to kbio with policy context
POST /v1/challenge/verify — Forward to kbio, apply policy to result
"""
from __future__ import annotations

import gzip
import importlib
import json

from fastapi import APIRouter, Request

_service = importlib.import_module("02_features.evaluate.service")
_kbio = importlib.import_module("02_features.evaluate.kbio_client")
_errors = importlib.import_module("01_core.errors")
_config = importlib.import_module("01_core.config")
_resp = importlib.import_module("01_core.response")

router = APIRouter(tags=["kprotect-evaluate"])


@router.post("/v1/evaluate")
async def evaluate(request: Request) -> dict:
    """Main evaluation endpoint. Receives SDK batch, calls kbio, runs policies."""
    # For V1, use a fixed org_id. In production, extract from API key.
    org_id = request.headers.get("X-KP-Org-Id", "default-org")
    actor_id = request.headers.get("X-KP-Key-Id", "sdk")

    # Handle gzip
    body = await request.body()
    if request.headers.get("content-encoding") == "gzip":
        body = gzip.decompress(body)

    payload = json.loads(body)

    result = await _service.evaluate(payload, org_id=org_id, actor_id=actor_id)
    return _resp.success_response(result)


@router.post("/v1/challenge/generate")
async def challenge_generate(request: Request) -> dict:
    """Forward challenge generation to kbio."""
    settings = _config.get_settings()
    body = await request.json()

    import httpx
    async with httpx.AsyncClient(base_url=settings.kbio_api_url) as client:
        resp = await client.post(
            "/v1/internal/challenge/generate",
            json=body,
            headers={"X-Internal-Service-Token": settings.kbio_service_token},
        )
        if resp.status_code in (200, 201):
            return resp.json()
        raise _errors.AppError("KBIO_ERROR", f"kbio returned {resp.status_code}", resp.status_code)


@router.post("/v1/challenge/verify")
async def challenge_verify(request: Request) -> dict:
    """Forward challenge verification to kbio."""
    settings = _config.get_settings()
    body = await request.json()

    import httpx
    async with httpx.AsyncClient(base_url=settings.kbio_api_url) as client:
        resp = await client.post(
            "/v1/internal/challenge/verify",
            json=body,
            headers={"X-Internal-Service-Token": settings.kbio_service_token},
        )
        if resp.status_code == 200:
            return resp.json()
        raise _errors.AppError("KBIO_ERROR", f"kbio returned {resp.status_code}", resp.status_code)

"""Health routes — /v1/somaerp/health (proxy round-trip check)."""

from __future__ import annotations

from importlib import import_module

from fastapi import APIRouter, Request

_service = import_module("apps.somaerp.backend.02_features.00_health.service")
_response = import_module("apps.somaerp.backend.01_core.response")

router = APIRouter(prefix="/v1/somaerp", tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict:
    config = request.app.state.config
    client = request.app.state.tennetctl
    started_at = request.app.state.started_at_monotonic
    result = await _service.get_health(
        config, client, started_at_monotonic=started_at,
    )
    return _response.ok(result.model_dump())

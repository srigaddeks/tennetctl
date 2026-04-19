"""
featureflags.apisix_routes — status + manual trigger endpoints for APISIX sync.

Routes:
  GET  /v1/flags/apisix/sync-status  → last PublishResult dict (from app.state)
  POST /v1/flags/apisix/sync         → run publish_once() now, return result
"""

from __future__ import annotations

from dataclasses import asdict
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_response: Any = import_module("backend.01_core.response")
_apisix_worker: Any = import_module(
    "backend.02_features.09_featureflags.apisix_worker"
)

router = APIRouter(prefix="/v1/flags/apisix", tags=["featureflags.apisix"])


@router.get("/sync-status", status_code=200)
async def sync_status_route(request: Request) -> dict:
    """Return the most recent PublishResult from the background worker.

    Empty dict if the worker hasn't completed a cycle yet (e.g. fresh boot).
    """
    status = getattr(request.app.state, "apisix_sync_status", None) or {}
    return _response.success(status)


@router.post("/sync", status_code=200)
async def sync_now_route(request: Request) -> dict:
    """Force an immediate publish cycle. Returns the fresh PublishResult.

    Useful for admin UI "Sync now" action + smoke tests from CI.
    """
    pool = request.app.state.pool
    result = await _apisix_worker.publish_once(pool)
    request.app.state.apisix_sync_status = asdict(result)
    return _response.success(asdict(result))

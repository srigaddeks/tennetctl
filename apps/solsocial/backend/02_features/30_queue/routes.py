"""Queue routes — /v1/queues."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_service = import_module("apps.solsocial.backend.02_features.30_queue.service")
_schemas = import_module("apps.solsocial.backend.02_features.30_queue.schemas")
_authz = import_module("apps.solsocial.backend.01_core.authz")
_response = import_module("apps.solsocial.backend.01_core.response")

router = APIRouter(tags=["queues"])


@router.get("/v1/queues")
async def get_queue(request: Request, channel_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "queues.read")
        row = await _service.get_queue_for_channel(
            conn, channel_id=channel_id, workspace_id=identity["workspace_id"],
        )
    return _response.success(_schemas.QueueOut(**row).model_dump())


@router.put("/v1/queues")
async def upsert_queue(request: Request, payload: _schemas.QueueUpsert) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "queues.manage")
        row = await _service.upsert_queue(
            conn,
            org_id=identity["org_id"],
            workspace_id=identity["workspace_id"],
            channel_id=payload.channel_id,
            timezone=payload.timezone,
            slots=[s.model_dump() for s in payload.slots],
        )
    return _response.success(_schemas.QueueOut(**row).model_dump())

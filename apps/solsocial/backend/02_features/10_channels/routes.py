"""Channel routes — /v1/channels."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request, Response

_service = import_module("apps.solsocial.backend.02_features.10_channels.service")
_schemas = import_module("apps.solsocial.backend.02_features.10_channels.schemas")
_authz = import_module("apps.solsocial.backend.01_core.authz")
_response = import_module("apps.solsocial.backend.01_core.response")

router = APIRouter(tags=["channels"])


@router.get("/v1/channels")
async def list_channels(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "channels.read")
        items = await _service.list_channels(
            conn, workspace_id=identity["workspace_id"], limit=limit, offset=offset,
        )
    validated = [_schemas.ChannelOut(**r).model_dump() for r in items]
    return _response.success_list_response(validated, limit=limit, offset=offset)


@router.get("/v1/channels/{channel_id}")
async def get_channel(request: Request, channel_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "channels.read")
        row = await _service.get_channel(
            conn, channel_id=channel_id, workspace_id=identity["workspace_id"],
        )
    return _response.success(_schemas.ChannelOut(**row).model_dump())


@router.patch("/v1/channels/{channel_id}")
async def patch_channel(
    request: Request, channel_id: str, payload: _schemas.ChannelPatch,
) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "channels.connect")
        row = await _service.patch_channel(
            conn,
            channel_id=channel_id,
            workspace_id=identity["workspace_id"],
            display_name=payload.display_name,
            avatar_url=payload.avatar_url,
        )
    return _response.success(_schemas.ChannelOut(**row).model_dump())


@router.delete("/v1/channels/{channel_id}", response_class=Response, status_code=204)
async def delete_channel(request: Request, channel_id: str) -> Response:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "channels.remove")
        await _service.disconnect_channel(
            conn, channel_id=channel_id, workspace_id=identity["workspace_id"],
        )
    return Response(status_code=204)

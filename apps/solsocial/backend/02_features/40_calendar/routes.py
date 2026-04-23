"""Calendar — read-only aggregate view over scheduled and published posts."""

from __future__ import annotations

from datetime import datetime
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request

_authz = import_module("apps.solsocial.backend.01_core.authz")
_response = import_module("apps.solsocial.backend.01_core.response")

SCHEMA = '"10_solsocial"'

router = APIRouter(tags=["calendar"])


@router.get("/v1/calendar")
async def list_calendar(
    request: Request,
    start: datetime = Query(...),
    end: datetime = Query(...),
) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "posts.read")
        rows = await conn.fetch(
            f'SELECT id, channel_id, status, body, scheduled_at, published_at '
            f'FROM {SCHEMA}.v_posts WHERE workspace_id = $1 '
            'AND COALESCE(scheduled_at, published_at) BETWEEN $2 AND $3 '
            'ORDER BY COALESCE(scheduled_at, published_at)',
            identity["workspace_id"], start, end,
        )
    items = [dict(r) for r in rows]
    return _response.success({"items": items, "start": start, "end": end})

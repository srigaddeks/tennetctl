"""kprotect decisions routes — read-only decision history.

GET /v1/kprotect/decisions              — list decisions (filtered, paginated)
GET /v1/kprotect/decisions/{id}         — get one decision + detail rows
"""

from __future__ import annotations

import importlib
from datetime import datetime

from fastapi import APIRouter, Query

_db = importlib.import_module("01_core.db")
_service = importlib.import_module("02_features.decisions.service")
_resp = importlib.import_module("01_core.response")

router = APIRouter(prefix="/v1/kprotect/decisions", tags=["decisions"])


@router.get("")
async def list_decisions(
    org_id: str = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_hash: str | None = Query(default=None),
    outcome: str | None = Query(default=None),
    action: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
) -> dict:
    filters = {
        "user_hash": user_hash,
        "outcome": outcome,
        "action": action,
        "since": since,
        "until": until,
    }
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.list_decisions(
            conn,
            org_id,
            limit=limit,
            offset=offset,
            filters=filters,
        )
    return _resp.success_list_response(
        result["items"],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )


@router.get("/{decision_id}")
async def get_decision(decision_id: str) -> dict:
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        row = await _service.get_decision(conn, decision_id)
    return _resp.success_response(row)

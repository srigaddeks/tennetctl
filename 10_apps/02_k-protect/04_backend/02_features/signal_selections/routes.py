"""kprotect signal_selections routes.

GET    /v1/kprotect/signal-selections          -- list
POST   /v1/kprotect/signal-selections          -- create (201)
GET    /v1/kprotect/signal-selections/{id}     -- get one
PATCH  /v1/kprotect/signal-selections/{id}     -- update
DELETE /v1/kprotect/signal-selections/{id}     -- soft-delete (204)
POST   /v1/kprotect/signal-selections/bulk     -- bulk create (201)
"""

from __future__ import annotations

import importlib

from fastapi import APIRouter, Query
from fastapi.responses import Response

_db = importlib.import_module("01_core.db")
_service = importlib.import_module("02_features.signal_selections.service")
_resp = importlib.import_module("01_core.response")
_schemas = importlib.import_module("02_features.signal_selections.schemas")

router = APIRouter(prefix="/v1/kprotect/signal-selections", tags=["signal-selections"])


@router.get("")
async def list_signal_selections(
    org_id: str = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.list_selections(conn, org_id, limit=limit, offset=offset)
    return _resp.success_list_response(
        result["items"],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )


@router.post("", status_code=201)
async def create_signal_selection(
    body: _schemas.CreateSignalSelectionRequest,  # type: ignore[name-defined]
) -> dict:
    pool = _db.get_pool()
    actor_id = "system"  # No JWT in V1 -- replaced when auth is added
    async with pool.acquire() as conn:
        row = await _service.create_selection(
            conn,
            org_id=body.org_id,  # type: ignore[attr-defined]
            signal_code=body.signal_code,
            config_overrides=body.config_overrides,
            notes=body.notes,
            actor_id=actor_id,
        )
    return _resp.success_response(row)


@router.get("/{selection_id}")
async def get_signal_selection(selection_id: str) -> dict:
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        row = await _service.get_selection(conn, selection_id)
    return _resp.success_response(row)


@router.patch("/{selection_id}")
async def patch_signal_selection(
    selection_id: str,
    body: _schemas.PatchSignalSelectionRequest,  # type: ignore[name-defined]
) -> dict:
    pool = _db.get_pool()
    actor_id = "system"
    async with pool.acquire() as conn:
        row = await _service.update_selection(
            conn,
            selection_id,
            config_overrides=body.config_overrides,
            notes=body.notes,
            is_active=body.is_active,
            actor_id=actor_id,
        )
    return _resp.success_response(row)


@router.delete("/{selection_id}", status_code=204)
async def delete_signal_selection(selection_id: str) -> Response:
    pool = _db.get_pool()
    actor_id = "system"
    async with pool.acquire() as conn:
        await _service.delete_selection(conn, selection_id, actor_id=actor_id)
    return Response(status_code=204)


@router.post("/bulk", status_code=201)
async def bulk_create_signal_selections(
    body: _schemas.BulkCreateSignalSelectionsRequest,  # type: ignore[name-defined]
) -> dict:
    pool = _db.get_pool()
    actor_id = "system"
    async with pool.acquire() as conn:
        rows = await _service.bulk_create(
            conn,
            org_id=body.org_id,  # type: ignore[attr-defined]
            signal_codes=body.signal_codes,
            config_overrides=body.config_overrides,
            actor_id=actor_id,
        )
    return _resp.success_response(rows)

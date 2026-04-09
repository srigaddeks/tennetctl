"""kprotect policy_selections routes.

GET    /v1/kprotect/policy-selections          — list
POST   /v1/kprotect/policy-selections          — create (201)
GET    /v1/kprotect/policy-selections/{id}     — get one
PATCH  /v1/kprotect/policy-selections/{id}     — update
DELETE /v1/kprotect/policy-selections/{id}     — soft-delete (204)
"""

from __future__ import annotations

import importlib

from fastapi import APIRouter, Query
from fastapi.responses import Response

_db = importlib.import_module("01_core.db")
_service = importlib.import_module("02_features.policy_selections.service")
_resp = importlib.import_module("01_core.response")
_schemas = importlib.import_module("02_features.policy_selections.schemas")

router = APIRouter(prefix="/v1/kprotect/policy-selections", tags=["policy-selections"])


@router.get("")
async def list_policy_selections(
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
async def create_policy_selection(
    body: _schemas.CreatePolicySelectionRequest,  # type: ignore[name-defined]
) -> dict:
    pool = _db.get_pool()
    actor_id = "system"  # No JWT in V1 — replaced when auth is added
    async with pool.acquire() as conn:
        row = await _service.create_selection(
            conn,
            org_id=body.org_id,  # type: ignore[attr-defined]
            predefined_policy_code=body.predefined_policy_code,
            priority=body.priority,
            config_overrides=body.config_overrides,
            notes=body.notes,
            policy_category=body.policy_category,
            policy_name=body.policy_name,
            actor_id=actor_id,
        )
    return _resp.success_response(row)


@router.get("/{selection_id}")
async def get_policy_selection(selection_id: str) -> dict:
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        row = await _service.get_selection(conn, selection_id)
    return _resp.success_response(row)


@router.patch("/{selection_id}")
async def patch_policy_selection(
    selection_id: str,
    body: _schemas.PatchPolicySelectionRequest,  # type: ignore[name-defined]
) -> dict:
    pool = _db.get_pool()
    actor_id = "system"
    async with pool.acquire() as conn:
        row = await _service.patch_selection(
            conn,
            selection_id,
            priority=body.priority,
            config_overrides=body.config_overrides,
            notes=body.notes,
            is_active=body.is_active,
            actor_id=actor_id,
        )
    return _resp.success_response(row)


@router.delete("/{selection_id}", status_code=204)
async def delete_policy_selection(selection_id: str) -> Response:
    pool = _db.get_pool()
    actor_id = "system"
    async with pool.acquire() as conn:
        await _service.delete_selection(conn, selection_id, actor_id=actor_id)
    return Response(status_code=204)

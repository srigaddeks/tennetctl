"""kprotect policy_sets routes.

GET    /v1/kprotect/policy-sets          — list
POST   /v1/kprotect/policy-sets          — create (201)
GET    /v1/kprotect/policy-sets/{id}     — get one
PATCH  /v1/kprotect/policy-sets/{id}     — update
DELETE /v1/kprotect/policy-sets/{id}     — soft-delete (204)
"""

from __future__ import annotations

import importlib

from fastapi import APIRouter, Query
from fastapi.responses import Response

_db = importlib.import_module("01_core.db")
_service = importlib.import_module("02_features.policy_sets.service")
_resp = importlib.import_module("01_core.response")
_schemas = importlib.import_module("02_features.policy_sets.schemas")

router = APIRouter(prefix="/v1/kprotect/policy-sets", tags=["policy-sets"])


@router.get("")
async def list_policy_sets(
    org_id: str = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.list_policy_sets(conn, org_id, limit=limit, offset=offset)
    return _resp.success_list_response(
        result["items"],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )


@router.post("", status_code=201)
async def create_policy_set(
    body: _schemas.CreatePolicySetRequest,  # type: ignore[name-defined]
) -> dict:
    pool = _db.get_pool()
    actor_id = "system"
    async with pool.acquire() as conn:
        row = await _service.create_policy_set(
            conn,
            org_id=body.org_id,
            code=body.code,
            name=body.name,
            description=body.description,
            evaluation_mode=body.evaluation_mode,
            is_default=body.is_default,
            member_selection_ids=[m.model_dump() for m in body.member_selection_ids],
            actor_id=actor_id,
        )
    return _resp.success_response(row)


@router.get("/{policy_set_id}")
async def get_policy_set(policy_set_id: str) -> dict:
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        row = await _service.get_policy_set(conn, policy_set_id)
    return _resp.success_response(row)


@router.patch("/{policy_set_id}")
async def patch_policy_set(
    policy_set_id: str,
    body: _schemas.PatchPolicySetRequest,  # type: ignore[name-defined]
) -> dict:
    pool = _db.get_pool()
    actor_id = "system"
    members = (
        [m.model_dump() for m in body.member_selection_ids]
        if body.member_selection_ids is not None
        else None
    )
    async with pool.acquire() as conn:
        row = await _service.patch_policy_set(
            conn,
            policy_set_id,
            name=body.name,
            description=body.description,
            evaluation_mode=body.evaluation_mode,
            is_default=body.is_default,
            member_selection_ids=members,
            actor_id=actor_id,
        )
    return _resp.success_response(row)


@router.delete("/{policy_set_id}", status_code=204)
async def delete_policy_set(policy_set_id: str) -> Response:
    pool = _db.get_pool()
    actor_id = "system"
    async with pool.acquire() as conn:
        await _service.delete_policy_set(conn, policy_set_id, actor_id=actor_id)
    return Response(status_code=204)

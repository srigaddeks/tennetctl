"""Capability catalog + role grants API."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")

_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.06_capabilities.service"
)
_schemas: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.06_capabilities.schemas"
)

router = APIRouter(tags=["capabilities"])


def _require_user(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    return user_id


@router.get("/v1/capabilities")
async def get_capability_catalog(request: Request):
    _require_user(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        data = await _service.get_catalog(conn)
    return _response.success_response(data)


@router.get("/v1/roles/{role_id}/grants")
async def get_role_grants(role_id: str, request: Request):
    _require_user(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        data = await _service.get_role_grants(conn, role_id)
    return _response.success_response(data)


@router.post("/v1/roles/{role_id}/grants", status_code=201)
async def post_role_grants(
    role_id: str,
    payload: _schemas.GrantRequest,
    request: Request,
):
    actor_id = _require_user(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _service.grant_permissions(
                conn,
                role_id=role_id,
                permission_codes=payload.permission_codes,
                actor_id=actor_id,
            )
        data = await _service.get_role_grants(conn, role_id)
    return _response.success_response(data)


@router.delete(
    "/v1/roles/{role_id}/grants/{permission_code}",
    status_code=204,
)
async def delete_role_grant(
    role_id: str,
    permission_code: str,
    request: Request,
):
    actor_id = _require_user(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        async with conn.transaction():
            await _service.revoke_permission(
                conn,
                role_id=role_id,
                permission_code=permission_code,
                actor_id=actor_id,
            )
    return None

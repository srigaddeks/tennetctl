"""Kitchen capacity routes — /v1/somaerp/geography/kitchens/{kitchen_id}/capacity."""

from __future__ import annotations

from datetime import date
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Body, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.16_kitchen_capacity.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.16_kitchen_capacity.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")

router = APIRouter(
    prefix="/v1/somaerp/geography/kitchens",
    tags=["geography", "kitchen_capacity"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("/{kitchen_id}/capacity")
async def list_capacity(
    request: Request,
    kitchen_id: str,
    product_line_id: str | None = Query(default=None),
    valid_on: date | None = Query(default=None),
    include_history: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_capacity(
            conn,
            tenant_id=workspace_id,
            kitchen_id=kitchen_id,
            product_line_id=product_line_id,
            valid_on=valid_on,
            include_history=include_history,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.CapacityOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/{kitchen_id}/capacity", status_code=201)
async def create_capacity(
    request: Request,
    kitchen_id: str,
    payload: Any = Body(...),
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    if isinstance(payload, list):
        items = [_schemas.CapacityCreate(**p) for p in payload]
    else:
        items = [_schemas.CapacityCreate(**payload)]

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    created: list[dict] = []
    async with pool.acquire() as conn:
        for item in items:
            row = await _service.create_capacity(
                conn,
                tennetctl=tennetctl,
                tenant_id=workspace_id,
                actor_user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                kitchen_id=kitchen_id,
                data=item.model_dump(mode="python"),
            )
            created.append(
                _schemas.CapacityOut(**row).model_dump(mode="json"),
            )
    return _response.ok(created if isinstance(payload, list) else created[0])


@router.get("/{kitchen_id}/capacity/{capacity_id}")
async def get_capacity(
    request: Request, kitchen_id: str, capacity_id: str,
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_capacity(
            conn,
            tenant_id=workspace_id,
            kitchen_id=kitchen_id,
            capacity_id=capacity_id,
        )
    return _response.ok(_schemas.CapacityOut(**row).model_dump(mode="json"))


@router.patch("/{kitchen_id}/capacity/{capacity_id}")
async def close_capacity(
    request: Request,
    kitchen_id: str,
    capacity_id: str,
    payload: _schemas.CapacityClosePatch,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.close_capacity(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            kitchen_id=kitchen_id,
            capacity_id=capacity_id,
            valid_to=payload.valid_to,
        )
    return _response.ok(_schemas.CapacityOut(**row).model_dump(mode="json"))


@router.delete(
    "/{kitchen_id}/capacity/{capacity_id}",
    status_code=204,
    response_class=Response,
)
async def delete_capacity(
    request: Request, kitchen_id: str, capacity_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_capacity(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            kitchen_id=kitchen_id,
            capacity_id=capacity_id,
        )
    return Response(status_code=204)

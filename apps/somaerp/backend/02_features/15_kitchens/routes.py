"""Kitchen routes — /v1/somaerp/geography/kitchens."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Body, Query, Request, Response

_service = import_module("apps.somaerp.backend.02_features.15_kitchens.service")
_schemas = import_module("apps.somaerp.backend.02_features.15_kitchens.schemas")
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")

router = APIRouter(
    prefix="/v1/somaerp/geography",
    tags=["geography", "kitchens"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("/kitchens")
async def list_kitchens(
    request: Request,
    location_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_kitchens(
            conn,
            tenant_id=workspace_id,
            location_id=location_id,
            status=status,
            q=q,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.KitchenOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/kitchens", status_code=201)
async def create_kitchen(
    request: Request,
    payload: Any = Body(...),
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    if isinstance(payload, list):
        items = [_schemas.KitchenCreate(**p) for p in payload]
    else:
        items = [_schemas.KitchenCreate(**payload)]

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    created: list[dict] = []
    async with pool.acquire() as conn:
        for item in items:
            row = await _service.create_kitchen(
                conn,
                tennetctl=tennetctl,
                tenant_id=workspace_id,
                actor_user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                data=item.model_dump(mode="python"),
            )
            created.append(_schemas.KitchenOut(**row).model_dump(mode="json"))
    return _response.ok(created if isinstance(payload, list) else created[0])


@router.get("/kitchens/{kitchen_id}")
async def get_kitchen(request: Request, kitchen_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_kitchen(
            conn, tenant_id=workspace_id, kitchen_id=kitchen_id,
        )
    return _response.ok(_schemas.KitchenOut(**row).model_dump(mode="json"))


@router.patch("/kitchens/{kitchen_id}")
async def patch_kitchen(
    request: Request,
    kitchen_id: str,
    payload: _schemas.KitchenUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_kitchen(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            kitchen_id=kitchen_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.KitchenOut(**row).model_dump(mode="json"))


@router.delete(
    "/kitchens/{kitchen_id}",
    status_code=204,
    response_class=Response,
)
async def delete_kitchen(request: Request, kitchen_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_kitchen(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            kitchen_id=kitchen_id,
        )
    return Response(status_code=204)

"""Equipment routes — /v1/somaerp/equipment + nested under /geography/kitchens/{id}/equipment.

Two routers are exported:
- `router`                  — /v1/somaerp/equipment + /v1/somaerp/equipment/categories
- `kitchen_equipment_router` — /v1/somaerp/geography/kitchens/{kitchen_id}/equipment
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Body, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.45_equipment.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.45_equipment.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")


router = APIRouter(
    prefix="/v1/somaerp/equipment",
    tags=["equipment"],
)


kitchen_equipment_router = APIRouter(
    prefix="/v1/somaerp/geography/kitchens",
    tags=["equipment", "kitchen"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


# ── Categories (read-only) ──────────────────────────────────────────────


@router.get("/categories")
async def list_categories(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_categories(conn)
    data = [
        _schemas.EquipmentCategoryOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


# ── Equipment CRUD ──────────────────────────────────────────────────────


@router.get("")
async def list_equipment(
    request: Request,
    category_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_equipment(
            conn,
            tenant_id=workspace_id,
            category_id=category_id,
            status=status,
            q=q,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.EquipmentOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("", status_code=201)
async def create_equipment(request: Request, payload: Any = Body(...)) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    if isinstance(payload, list):
        items = [_schemas.EquipmentCreate(**p) for p in payload]
    else:
        items = [_schemas.EquipmentCreate(**payload)]

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    created: list[dict] = []
    async with pool.acquire() as conn:
        for item in items:
            row = await _service.create_equipment(
                conn,
                tennetctl=tennetctl,
                tenant_id=workspace_id,
                actor_user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                data=item.model_dump(mode="python"),
            )
            created.append(
                _schemas.EquipmentOut(**row).model_dump(mode="json"),
            )
    return _response.ok(created if isinstance(payload, list) else created[0])


@router.get("/{equipment_id}")
async def get_equipment(request: Request, equipment_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_equipment(
            conn, tenant_id=workspace_id, equipment_id=equipment_id,
        )
    return _response.ok(_schemas.EquipmentOut(**row).model_dump(mode="json"))


@router.patch("/{equipment_id}")
async def patch_equipment(
    request: Request,
    equipment_id: str,
    payload: _schemas.EquipmentUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_equipment(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            equipment_id=equipment_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.EquipmentOut(**row).model_dump(mode="json"))


@router.delete(
    "/{equipment_id}", status_code=204, response_class=Response,
)
async def delete_equipment(request: Request, equipment_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_equipment(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            equipment_id=equipment_id,
        )
    return Response(status_code=204)


# ── Kitchen <-> Equipment link (SECOND ROUTER) ─────────────────────────


@kitchen_equipment_router.get("/{kitchen_id}/equipment")
async def list_kitchen_equipment(request: Request, kitchen_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_kitchen_equipment(
            conn, tenant_id=workspace_id, kitchen_id=kitchen_id,
        )
    data = [
        _schemas.KitchenEquipmentLinkOut(**r).model_dump(mode="json")
        for r in rows
    ]
    return _response.ok(data)


@kitchen_equipment_router.post(
    "/{kitchen_id}/equipment", status_code=201,
)
async def attach_equipment(
    request: Request,
    kitchen_id: str,
    payload: _schemas.KitchenEquipmentLinkCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.attach_equipment_to_kitchen(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            kitchen_id=kitchen_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(
        _schemas.KitchenEquipmentLinkOut(**row).model_dump(mode="json"),
    )


@kitchen_equipment_router.delete(
    "/{kitchen_id}/equipment/{equipment_id}",
    status_code=204,
    response_class=Response,
)
async def detach_equipment(
    request: Request, kitchen_id: str, equipment_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.detach_equipment_from_kitchen(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            kitchen_id=kitchen_id,
            equipment_id=equipment_id,
        )
    return Response(status_code=204)

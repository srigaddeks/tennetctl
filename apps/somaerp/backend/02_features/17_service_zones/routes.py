"""Service zone routes — /v1/somaerp/geography/service-zones."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Body, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.17_service_zones.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.17_service_zones.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")

router = APIRouter(
    prefix="/v1/somaerp/geography",
    tags=["geography", "service_zones"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("/service-zones")
async def list_zones(
    request: Request,
    kitchen_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_zones(
            conn,
            tenant_id=workspace_id,
            kitchen_id=kitchen_id,
            status=status,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.ServiceZoneOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/service-zones", status_code=201)
async def create_zone(
    request: Request,
    payload: Any = Body(...),
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    if isinstance(payload, list):
        items = [_schemas.ServiceZoneCreate(**p) for p in payload]
    else:
        items = [_schemas.ServiceZoneCreate(**payload)]

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    created: list[dict] = []
    async with pool.acquire() as conn:
        for item in items:
            row = await _service.create_zone(
                conn,
                tennetctl=tennetctl,
                tenant_id=workspace_id,
                actor_user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                data=item.model_dump(),
            )
            created.append(
                _schemas.ServiceZoneOut(**row).model_dump(mode="json"),
            )
    return _response.ok(created if isinstance(payload, list) else created[0])


@router.get("/service-zones/{zone_id}")
async def get_zone(request: Request, zone_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_zone(
            conn, tenant_id=workspace_id, zone_id=zone_id,
        )
    return _response.ok(_schemas.ServiceZoneOut(**row).model_dump(mode="json"))


@router.patch("/service-zones/{zone_id}")
async def patch_zone(
    request: Request,
    zone_id: str,
    payload: _schemas.ServiceZoneUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_zone(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            zone_id=zone_id,
            patch=payload.model_dump(exclude_unset=True),
        )
    return _response.ok(_schemas.ServiceZoneOut(**row).model_dump(mode="json"))


@router.delete(
    "/service-zones/{zone_id}",
    status_code=204,
    response_class=Response,
)
async def delete_zone(request: Request, zone_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_zone(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            zone_id=zone_id,
        )
    return Response(status_code=204)

"""Geography location routes — /v1/somaerp/geography/{regions,locations}.

Mounted on the shared prefix /v1/somaerp/geography (tags include both
"geography" and "locations") so the regions endpoint (read-only) lives
alongside the locations CRUD.

Bulk POST is supported: body may be a single object or an array.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Body, Query, Request, Response

_service = import_module("apps.somaerp.backend.02_features.10_locations.service")
_schemas = import_module("apps.somaerp.backend.02_features.10_locations.schemas")
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")

router = APIRouter(
    prefix="/v1/somaerp/geography",
    tags=["geography", "locations"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


# ── Regions (read-only) ───────────────────────────────────────────────────

@router.get("/regions")
async def list_regions(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_regions(conn)
    validated = [_schemas.RegionOut(**r).model_dump() for r in rows]
    return _response.ok(validated)


# ── Locations ─────────────────────────────────────────────────────────────

@router.get("/locations")
async def list_locations(
    request: Request,
    region_id: int | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_locations(
            conn,
            tenant_id=workspace_id,
            region_id=region_id,
            q=q,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.LocationOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/locations", status_code=201)
async def create_location(
    request: Request,
    payload: Any = Body(...),
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    # Bulk POST: body is a JSON array of LocationCreate.
    if isinstance(payload, list):
        items = [_schemas.LocationCreate(**p) for p in payload]
    else:
        items = [_schemas.LocationCreate(**payload)]

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    created: list[dict] = []
    async with pool.acquire() as conn:
        for item in items:
            row = await _service.create_location(
                conn,
                tennetctl=tennetctl,
                tenant_id=workspace_id,
                actor_user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                data=item.model_dump(),
            )
            created.append(_schemas.LocationOut(**row).model_dump(mode="json"))
    # Preserve shape: single-object body returns a single object.
    return _response.ok(created if isinstance(payload, list) else created[0])


@router.get("/locations/{location_id}")
async def get_location(request: Request, location_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_location(
            conn, tenant_id=workspace_id, location_id=location_id,
        )
    return _response.ok(_schemas.LocationOut(**row).model_dump(mode="json"))


@router.patch("/locations/{location_id}")
async def patch_location(
    request: Request,
    location_id: str,
    payload: _schemas.LocationUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_location(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            location_id=location_id,
            patch=payload.model_dump(exclude_unset=True),
        )
    return _response.ok(_schemas.LocationOut(**row).model_dump(mode="json"))


@router.delete(
    "/locations/{location_id}",
    status_code=204,
    response_class=Response,
)
async def delete_location(request: Request, location_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_location(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            location_id=location_id,
        )
    return Response(status_code=204)

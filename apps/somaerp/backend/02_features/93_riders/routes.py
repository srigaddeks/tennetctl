"""Riders routes — /v1/somaerp/delivery/rider-roles + /riders."""

from __future__ import annotations

from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.93_riders.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.93_riders.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")


router = APIRouter(
    prefix="/v1/somaerp/delivery",
    tags=["delivery", "riders"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


# ── Rider roles (read-only) ──────────────────────────────────────────────


@router.get("/rider-roles")
async def list_rider_roles(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_roles(conn)
    data = [
        _schemas.RiderRoleOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


# ── Riders CRUD ─────────────────────────────────────────────────────────


@router.get("/riders")
async def list_riders(
    request: Request,
    status: str | None = Query(default=None),
    role_id: int | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_riders(
            conn,
            tenant_id=workspace_id,
            status=status,
            role_id=role_id,
            q=q,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.RiderOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/riders", status_code=201)
async def create_rider(
    request: Request, payload: _schemas.RiderCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_rider(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(_schemas.RiderOut(**row).model_dump(mode="json"))


@router.get("/riders/{rider_id}")
async def get_rider(request: Request, rider_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_rider(
            conn, tenant_id=workspace_id, rider_id=rider_id,
        )
    return _response.ok(_schemas.RiderOut(**row).model_dump(mode="json"))


@router.patch("/riders/{rider_id}")
async def patch_rider(
    request: Request, rider_id: str, payload: _schemas.RiderUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_rider(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            rider_id=rider_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.RiderOut(**row).model_dump(mode="json"))


@router.delete(
    "/riders/{rider_id}", status_code=204, response_class=Response,
)
async def delete_rider(request: Request, rider_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_rider(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            rider_id=rider_id,
        )
    return Response(status_code=204)

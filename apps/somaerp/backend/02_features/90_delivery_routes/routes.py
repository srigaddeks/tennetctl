"""Delivery routes routes — /v1/somaerp/delivery/routes + /routes/{id}/customers."""

from __future__ import annotations

from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.90_delivery_routes.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.90_delivery_routes.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")


router = APIRouter(
    prefix="/v1/somaerp/delivery",
    tags=["delivery", "routes"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


# ── Routes CRUD ──────────────────────────────────────────────────────


@router.get("/routes")
async def list_routes(
    request: Request,
    kitchen_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_routes(
            conn,
            tenant_id=workspace_id,
            kitchen_id=kitchen_id,
            status=status,
            q=q,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.RouteOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/routes", status_code=201)
async def create_route(
    request: Request, payload: _schemas.RouteCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_route(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(_schemas.RouteOut(**row).model_dump(mode="json"))


@router.get("/routes/{route_id}")
async def get_route(request: Request, route_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_route(
            conn, tenant_id=workspace_id, route_id=route_id,
        )
    return _response.ok(_schemas.RouteOut(**row).model_dump(mode="json"))


@router.patch("/routes/{route_id}")
async def patch_route(
    request: Request, route_id: str, payload: _schemas.RouteUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_route(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            route_id=route_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.RouteOut(**row).model_dump(mode="json"))


@router.delete(
    "/routes/{route_id}", status_code=204, response_class=Response,
)
async def delete_route(request: Request, route_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_route(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            route_id=route_id,
        )
    return Response(status_code=204)


# ── Route customers ──────────────────────────────────────────────────


@router.get("/routes/{route_id}/customers")
async def list_route_customers(request: Request, route_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_route_customers(
            conn, tenant_id=workspace_id, route_id=route_id,
        )
    data = [
        _schemas.RouteCustomerLinkOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


@router.post("/routes/{route_id}/customers", status_code=201)
async def attach_route_customer(
    request: Request,
    route_id: str,
    payload: _schemas.RouteCustomerAttach,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.attach_route_customer(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            route_id=route_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(
        _schemas.RouteCustomerLinkOut(**row).model_dump(mode="json"),
    )


@router.delete(
    "/routes/{route_id}/customers/{customer_id}",
    status_code=204,
    response_class=Response,
)
async def detach_route_customer(
    request: Request, route_id: str, customer_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.detach_route_customer(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            route_id=route_id,
            customer_id=customer_id,
        )
    return Response(status_code=204)


@router.post("/routes/{route_id}/customers/reorder")
async def reorder_route_customers(
    request: Request,
    route_id: str,
    payload: _schemas.RouteCustomerReorder,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        rows = await _service.reorder_route_customers(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            route_id=route_id,
            customer_ids=payload.customer_ids,
        )
    data = [
        _schemas.RouteCustomerLinkOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)

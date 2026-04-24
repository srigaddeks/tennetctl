"""Customers routes — /v1/somaerp/customers/*.

Standard 5-endpoint shape. Filters: status, location_id, q.
"""

from __future__ import annotations

from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module("apps.somaerp.backend.02_features.80_customers.service")
_schemas = import_module("apps.somaerp.backend.02_features.80_customers.schemas")
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")


router = APIRouter(
    prefix="/v1/somaerp/customers",
    tags=["customers"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("")
async def list_customers(
    request: Request,
    status: str | None = Query(default=None),
    location_id: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_customers(
            conn,
            tenant_id=workspace_id,
            status=status,
            location_id=location_id,
            q=q,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.CustomerOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("", status_code=201)
async def create_customer(
    request: Request, payload: _schemas.CustomerCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_customer(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data=payload.model_dump(),
        )
    return _response.ok(_schemas.CustomerOut(**row).model_dump(mode="json"))


@router.get("/{customer_id}")
async def get_customer(request: Request, customer_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_customer(
            conn, tenant_id=workspace_id, customer_id=customer_id,
        )
    return _response.ok(_schemas.CustomerOut(**row).model_dump(mode="json"))


@router.patch("/{customer_id}")
async def patch_customer(
    request: Request,
    customer_id: str,
    payload: _schemas.CustomerUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_customer(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            customer_id=customer_id,
            patch=payload.model_dump(exclude_unset=True),
        )
    return _response.ok(_schemas.CustomerOut(**row).model_dump(mode="json"))


@router.delete(
    "/{customer_id}", status_code=204, response_class=Response,
)
async def delete_customer(request: Request, customer_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_customer(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            customer_id=customer_id,
        )
    return Response(status_code=204)

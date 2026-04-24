"""Address routes — /v1/somacrm/addresses."""

from __future__ import annotations

from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module("apps.somacrm.backend.02_features.20_addresses.service")
_schemas = import_module("apps.somacrm.backend.02_features.20_addresses.schemas")
_response = import_module("apps.somacrm.backend.01_core.response")
_errors = import_module("apps.somacrm.backend.01_core.errors")

router = APIRouter(prefix="/v1/somacrm/addresses", tags=["addresses"])


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("")
async def list_addresses(
    request: Request,
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        rows = await _service.list_addresses(
            conn, tenant_id=workspace_id, entity_type=entity_type,
            entity_id=entity_id, limit=limit, offset=offset,
        )
    return _response.ok([_schemas.AddressOut(**r).model_dump(mode="json") for r in rows])


@router.post("", status_code=201)
async def create_address(request: Request, payload: _schemas.AddressCreate) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.create_address(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            data=payload.model_dump(),
        )
    return _response.ok(_schemas.AddressOut(**row).model_dump(mode="json"))


@router.get("/{address_id}")
async def get_address(request: Request, address_id: str) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.get_address(conn, tenant_id=workspace_id, address_id=address_id)
    return _response.ok(_schemas.AddressOut(**row).model_dump(mode="json"))


@router.patch("/{address_id}")
async def patch_address(request: Request, address_id: str, payload: _schemas.AddressUpdate) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.update_address(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            address_id=address_id,
            patch=payload.model_dump(exclude_unset=True),
        )
    return _response.ok(_schemas.AddressOut(**row).model_dump(mode="json"))


@router.delete("/{address_id}", status_code=204, response_class=Response)
async def delete_address(request: Request, address_id: str) -> Response:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        await _service.soft_delete_address(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            address_id=address_id,
        )
    return Response(status_code=204)

"""Contact routes — /v1/somacrm/contacts."""

from __future__ import annotations

from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module("apps.somacrm.backend.02_features.10_contacts.service")
_schemas = import_module("apps.somacrm.backend.02_features.10_contacts.schemas")
_response = import_module("apps.somacrm.backend.01_core.response")
_errors = import_module("apps.somacrm.backend.01_core.errors")

router = APIRouter(prefix="/v1/somacrm/contacts", tags=["contacts"])


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("")
async def list_contacts(
    request: Request,
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    organization_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        rows = await _service.list_contacts(
            conn,
            tenant_id=workspace_id,
            q=q,
            status=status,
            organization_id=organization_id,
            limit=limit,
            offset=offset,
        )
    return _response.ok([_schemas.ContactOut(**r).model_dump(mode="json") for r in rows])


@router.post("", status_code=201)
async def create_contact(
    request: Request,
    payload: _schemas.ContactCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.create_contact(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            data=payload.model_dump(),
        )
    return _response.ok(_schemas.ContactOut(**row).model_dump(mode="json"))


@router.get("/{contact_id}")
async def get_contact(request: Request, contact_id: str) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.get_contact(conn, tenant_id=workspace_id, contact_id=contact_id)
    return _response.ok(_schemas.ContactOut(**row).model_dump(mode="json"))


@router.patch("/{contact_id}")
async def patch_contact(
    request: Request,
    contact_id: str,
    payload: _schemas.ContactUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.update_contact(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            contact_id=contact_id,
            patch=payload.model_dump(exclude_unset=True),
        )
    return _response.ok(_schemas.ContactOut(**row).model_dump(mode="json"))


@router.delete("/{contact_id}", status_code=204, response_class=Response)
async def delete_contact(request: Request, contact_id: str) -> Response:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        await _service.soft_delete_contact(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            contact_id=contact_id,
        )
    return Response(status_code=204)

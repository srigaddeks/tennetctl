"""Lead routes — /v1/somacrm/leads."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request, Response
from pydantic import BaseModel

_service = import_module("apps.somacrm.backend.02_features.25_leads.service")
_schemas = import_module("apps.somacrm.backend.02_features.25_leads.schemas")
_response = import_module("apps.somacrm.backend.01_core.response")
_errors = import_module("apps.somacrm.backend.01_core.errors")


class LeadConvertPayload(BaseModel):
    deal_title: str | None = None
    deal_value: float | None = None
    stage_id: str | None = None

router = APIRouter(prefix="/v1/somacrm/leads", tags=["leads"])


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("")
async def list_leads(
    request: Request,
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        rows = await _service.list_leads(conn, tenant_id=workspace_id, status=status, q=q, limit=limit, offset=offset)
    return _response.ok([_schemas.LeadOut(**r).model_dump(mode="json") for r in rows])


@router.post("", status_code=201)
async def create_lead(request: Request, payload: _schemas.LeadCreate) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.create_lead(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            data=payload.model_dump(),
        )
    return _response.ok(_schemas.LeadOut(**row).model_dump(mode="json"))


@router.get("/{lead_id}")
async def get_lead(request: Request, lead_id: str) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.get_lead(conn, tenant_id=workspace_id, lead_id=lead_id)
    return _response.ok(_schemas.LeadOut(**row).model_dump(mode="json"))


@router.patch("/{lead_id}")
async def patch_lead(request: Request, lead_id: str, payload: _schemas.LeadUpdate) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.update_lead(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            lead_id=lead_id,
            patch=payload.model_dump(exclude_unset=True),
        )
    return _response.ok(_schemas.LeadOut(**row).model_dump(mode="json"))


@router.post("/{lead_id}/convert", status_code=201)
async def convert_lead(
    request: Request,
    lead_id: str,
    payload: LeadConvertPayload = LeadConvertPayload(),
) -> dict:
    """Atomically converts a lead to a contact + deal in a single transaction."""
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        result = await _service.convert_lead_to_contact_deal(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            lead_id=lead_id,
            deal_title=payload.deal_title,
            deal_value=payload.deal_value,
            stage_id=payload.stage_id,
        )
    return _response.ok(result)


@router.delete("/{lead_id}", status_code=204, response_class=Response)
async def delete_lead(request: Request, lead_id: str) -> Response:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        await _service.soft_delete_lead(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            lead_id=lead_id,
        )
    return Response(status_code=204)

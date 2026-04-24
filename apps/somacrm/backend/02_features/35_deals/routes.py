"""Deal routes — /v1/somacrm/deals."""

from __future__ import annotations

from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module("apps.somacrm.backend.02_features.35_deals.service")
_schemas = import_module("apps.somacrm.backend.02_features.35_deals.schemas")
_response = import_module("apps.somacrm.backend.01_core.response")
_errors = import_module("apps.somacrm.backend.01_core.errors")

router = APIRouter(prefix="/v1/somacrm/deals", tags=["deals"])


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("")
async def list_deals(
    request: Request,
    status: str | None = Query(default=None),
    stage_id: str | None = Query(default=None),
    contact_id: str | None = Query(default=None),
    organization_id: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        rows = await _service.list_deals(
            conn, tenant_id=workspace_id, status=status, stage_id=stage_id,
            contact_id=contact_id, organization_id=organization_id,
            q=q, limit=limit, offset=offset,
        )
    return _response.ok([_schemas.DealOut(**r).model_dump(mode="json") for r in rows])


@router.post("", status_code=201)
async def create_deal(request: Request, payload: _schemas.DealCreate) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.create_deal(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            data=payload.model_dump(),
        )
    return _response.ok(_schemas.DealOut(**row).model_dump(mode="json"))


@router.get("/{deal_id}")
async def get_deal(request: Request, deal_id: str) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.get_deal(conn, tenant_id=workspace_id, deal_id=deal_id)
    return _response.ok(_schemas.DealOut(**row).model_dump(mode="json"))


@router.patch("/{deal_id}")
async def patch_deal(request: Request, deal_id: str, payload: _schemas.DealUpdate) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.update_deal(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            deal_id=deal_id,
            patch=payload.model_dump(exclude_unset=True),
        )
    return _response.ok(_schemas.DealOut(**row).model_dump(mode="json"))


@router.delete("/{deal_id}", status_code=204, response_class=Response)
async def delete_deal(request: Request, deal_id: str) -> Response:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        await _service.soft_delete_deal(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            deal_id=deal_id,
        )
    return Response(status_code=204)

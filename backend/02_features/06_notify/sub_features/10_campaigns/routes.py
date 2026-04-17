"""FastAPI routes for notify.campaigns."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.10_campaigns.service"
)
_schemas: Any = import_module(
    "backend.02_features.06_notify.sub_features.10_campaigns.schemas"
)
_del_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.repository"
)
_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")

router = APIRouter()

CampaignCreate = _schemas.CampaignCreate
CampaignPatch  = _schemas.CampaignPatch
CampaignRow    = _schemas.CampaignRow


def _require_auth(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    return user_id


@router.get("/v1/notify/campaigns", status_code=200)
async def list_campaigns_route(request: Request) -> dict:
    org_id = request.query_params.get("org_id")
    if not org_id:
        raise _errors.AppError("BAD_REQUEST", "org_id required.", 400)
    status_code = request.query_params.get("status")
    limit  = int(request.query_params.get("limit", 50))
    offset = int(request.query_params.get("offset", 0))

    async with request.app.state.pool.acquire() as conn:
        rows = await _service.list_campaigns(
            conn, org_id=org_id, status_code=status_code, limit=limit, offset=offset
        )
    items = [CampaignRow(**_coerce(r)).model_dump() for r in rows]
    return _response.success_response({"items": items, "total": len(items)})


@router.post("/v1/notify/campaigns", status_code=201)
async def create_campaign_route(body: CampaignCreate, request: Request) -> dict:
    user_id = _require_auth(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.create_campaign(
            conn, data=body.model_dump(), created_by=user_id
        )
    return _response.success_response(CampaignRow(**_coerce(row)).model_dump(), status_code=201)


@router.get("/v1/notify/campaigns/{campaign_id}", status_code=200)
async def get_campaign_route(campaign_id: str, request: Request) -> dict:
    async with request.app.state.pool.acquire() as conn:
        row = await _service.get_campaign(conn, campaign_id=campaign_id)
    if row is None:
        raise _errors.AppError("NOT_FOUND", f"campaign {campaign_id!r} not found.", 404)
    return _response.success_response(CampaignRow(**_coerce(row)).model_dump())


@router.patch("/v1/notify/campaigns/{campaign_id}", status_code=200)
async def update_campaign_route(
    campaign_id: str, body: CampaignPatch, request: Request
) -> dict:
    user_id = _require_auth(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.update_campaign(
            conn, campaign_id=campaign_id, data=body.model_dump(exclude_none=True), updated_by=user_id
        )
    if row is None:
        raise _errors.AppError("NOT_FOUND", f"campaign {campaign_id!r} not found.", 404)
    return _response.success_response(CampaignRow(**_coerce(row)).model_dump())


@router.get("/v1/notify/campaigns/{campaign_id}/stats", status_code=200)
async def get_campaign_stats_route(campaign_id: str, request: Request) -> dict:
    async with request.app.state.pool.acquire() as conn:
        stats = await _del_repo.campaign_stats(conn, campaign_id=campaign_id)
    return _response.success_response(stats)


@router.delete("/v1/notify/campaigns/{campaign_id}", status_code=204)
async def delete_campaign_route(campaign_id: str, request: Request) -> None:
    user_id = _require_auth(request)
    async with request.app.state.pool.acquire() as conn:
        await _service.delete_campaign(conn, campaign_id=campaign_id, updated_by=user_id)


def _coerce(row: dict) -> dict:
    """Convert asyncpg Record → plain dict with string timestamps."""
    out = dict(row)
    for k in ("scheduled_at", "created_at", "updated_at"):
        if out.get(k) is not None and not isinstance(out[k], str):
            out[k] = out[k].isoformat()
    if out.get("scheduled_at") is None:
        out["scheduled_at"] = None
    return out

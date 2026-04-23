"""Routes for /v1/provider-apps — per-workspace BYO OAuth apps.

Thin façade over tennetctl vault. Solsocial owns no credential storage.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request, Response

_service = import_module("apps.solsocial.backend.02_features.15_provider_apps.service")
_schemas = import_module("apps.solsocial.backend.02_features.15_provider_apps.schemas")
_authz = import_module("apps.solsocial.backend.01_core.authz")
_response = import_module("apps.solsocial.backend.01_core.response")

router = APIRouter(tags=["provider-apps"])


@router.get("/v1/provider-apps")
async def list_provider_apps(request: Request) -> Any:
    tennetctl = request.app.state.tennetctl
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "channels.connect")
    items = await _service.list_apps(
        tennetctl,
        workspace_id=identity["workspace_id"], org_id=identity["org_id"],
    )
    return _response.success({"items": items, "total": len(items)})


@router.put("/v1/provider-apps")
async def upsert_provider_app(request: Request, payload: _schemas.WorkspaceAppUpsert) -> Any:
    tennetctl = request.app.state.tennetctl
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "channels.connect")
    row = await _service.upsert_app(
        tennetctl,
        workspace_id=identity["workspace_id"], org_id=identity["org_id"],
        provider_code=payload.provider_code,
        client_id=payload.client_id,
        client_secret=payload.client_secret,
        redirect_uri_hint=payload.redirect_uri_hint,
        notes=payload.notes,
    )
    await tennetctl.emit_audit(
        event_key="solsocial.provider_apps.upserted", outcome="success",
        metadata={"provider": payload.provider_code, "vault_key": row["vault_key"]},
        actor_user_id=identity["user_id"], org_id=identity["org_id"],
        workspace_id=identity["workspace_id"],
    )
    return _response.success(row)


@router.delete(
    "/v1/provider-apps/{provider_code}",
    response_class=Response, status_code=204,
)
async def delete_provider_app(request: Request, provider_code: str) -> Response:
    tennetctl = request.app.state.tennetctl
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "channels.connect")
    await _service.delete_app(
        tennetctl,
        workspace_id=identity["workspace_id"],
        org_id=identity["org_id"],
        provider_code=provider_code,
    )
    return Response(status_code=204)

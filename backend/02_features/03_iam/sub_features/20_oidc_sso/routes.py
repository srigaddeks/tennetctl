"""iam.oidc_sso — provider management routes (session-required)."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.20_oidc_sso.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.20_oidc_sso.service"
)

OidcProviderCreate = _schemas.OidcProviderCreate
OidcProviderRow = _schemas.OidcProviderRow

router = APIRouter(prefix="/v1/iam/oidc-providers", tags=["iam.oidc_sso"])


def _require_org_id(request: Request) -> str:
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise _errors.UnauthorizedError("org context required")
    return org_id


def _build_ctx(request: Request, pool: Any) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=getattr(request.state, "user_id", None),
        session_id=getattr(request.state, "session_id", None),
        org_id=getattr(request.state, "org_id", None),
        workspace_id=getattr(request.state, "workspace_id", None),
        application_id=getattr(request.state, "application_id", None) or request.headers.get("x-application-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="admin",
        pool=pool,
        extras={"pool": pool},
    )


def _serialize(row: dict) -> dict:
    return OidcProviderRow(**row).model_dump(mode="json")


@router.get("")
async def list_oidc_providers(request: Request) -> Any:
    pool = request.app.state.pool
    org_id = _require_org_id(request)
    async with pool.acquire() as conn:
        providers = await _service.list_providers(conn, org_id)
    return _response.success([_serialize(p) for p in providers])


@router.post("", status_code=201)
async def create_oidc_provider(request: Request, body: OidcProviderCreate) -> Any:
    pool = request.app.state.pool
    org_id = _require_org_id(request)
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        provider = await _service.create_provider(pool, conn, ctx, org_id, body)
    return JSONResponse(content=_response.success(_serialize(provider)), status_code=201)


@router.delete("/{provider_id}", status_code=204)
async def delete_oidc_provider(provider_id: str, request: Request) -> None:
    pool = request.app.state.pool
    org_id = _require_org_id(request)
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        await _service.delete_provider(pool, conn, ctx, provider_id, org_id)

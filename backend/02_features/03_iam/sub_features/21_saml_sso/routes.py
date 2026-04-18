"""iam.saml_sso — FastAPI routes. CRUD for /v1/iam/saml-providers."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

_resp: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.21_saml_sso.service"
)
_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.21_saml_sso.schemas"
)
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")

SamlProviderCreate = _schemas.SamlProviderCreate
SamlProviderRow = _schemas.SamlProviderRow

router = APIRouter(prefix="/v1/iam/saml-providers", tags=["iam.saml_sso"])


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
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="admin",
        extras={"pool": pool},
    )


@router.get("")
async def list_providers(request: Request) -> Any:
    pool = request.app.state.pool
    org_id = _require_org_id(request)
    async with pool.acquire() as conn:
        rows = await _service.list_providers(conn, org_id)
    data = [SamlProviderRow(**r).model_dump(mode="json") for r in rows]
    return _resp.success_response(data)


@router.post("", status_code=201)
async def create_provider(request: Request, body: SamlProviderCreate) -> Any:
    pool = request.app.state.pool
    org_id = _require_org_id(request)
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        row = await _service.create_provider(pool, conn, ctx, org_id, body)
    return JSONResponse(
        content=_resp.success(SamlProviderRow(**row).model_dump(mode="json")),
        status_code=201,
    )


@router.delete("/{provider_id}", status_code=204)
async def delete_provider(provider_id: str, request: Request) -> None:
    pool = request.app.state.pool
    org_id = _require_org_id(request)
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        await _service.delete_provider(pool, conn, ctx, provider_id, org_id)

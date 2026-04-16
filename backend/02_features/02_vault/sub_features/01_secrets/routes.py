"""
vault.secrets — FastAPI routes.

Scope-aware (plan 07-03). HTTP routes are metadata-only; the plaintext HTTP view
(GET /v1/vault/{key}) was removed — secrets are never readable over HTTP after
the reveal-once flow at create/rotate time. VaultClient.get (in-process Python
API used by Phase 8 auth) remains the only read path.

Endpoints (4, down from 5):
  GET    /v1/vault                                 — list metadata + scope filters
  POST   /v1/vault                                 — create (returns metadata, reveal-once client-side)
  POST   /v1/vault/{key}/rotate                    — rotate (returns metadata, reveal-once client-side)
  DELETE /v1/vault/{key}                           — soft-delete
  (the item path carries ?scope=... &org_id=... &workspace_id=... query params
   when the caller needs to disambiguate beyond global scope)
"""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request, Response

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.02_vault.sub_features.01_secrets.schemas"
)
_service: Any = import_module(
    "backend.02_features.02_vault.sub_features.01_secrets.service"
)

SecretCreate = _schemas.SecretCreate
SecretRotate = _schemas.SecretRotate
SecretMeta = _schemas.SecretMeta

router = APIRouter(prefix="/v1/vault", tags=["vault.secrets"])


def _ensure_vault_available(request: Request) -> Any:
    config = request.app.state.config
    if not config.allow_unauthenticated_vault:
        raise _errors.AppError(
            code="VAULT_LOCKED",
            message=(
                "Vault routes are locked. Set TENNETCTL_ALLOW_UNAUTHENTICATED_VAULT=true "
                "for v0.2; auth gate arrives in phase 8."
            ),
            status_code=503,
        )
    vault = getattr(request.app.state, "vault", None)
    if vault is None:
        raise _errors.AppError(
            code="VAULT_UNAVAILABLE",
            message="Vault client not initialised. Enable the 'vault' module.",
            status_code=503,
        )
    return vault


def _build_ctx(request: Request, pool: Any, vault: Any, *, audit_category: str) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=request.headers.get("x-user-id"),
        session_id=request.headers.get("x-session-id"),
        org_id=request.headers.get("x-org-id"),
        workspace_id=request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category=audit_category,
        extras={"pool": pool, "vault": vault},
    )


@router.get("", status_code=200)
async def list_secrets_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    scope: str | None = None,
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> dict:
    vault = _ensure_vault_available(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, vault, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_secrets(
            conn, ctx,
            limit=limit, offset=offset,
            scope=scope, org_id=org_id, workspace_id=workspace_id,
        )
    data = [SecretMeta(**row).model_dump() for row in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_secret_route(request: Request, body: SecretCreate) -> dict:
    vault = _ensure_vault_available(request)
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, vault, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            secret = await _service.create_secret(
                pool, conn, ctx,
                vault_client=vault,
                key=body.key,
                value=body.value,
                description=body.description,
                scope=body.scope,
                org_id=body.org_id,
                workspace_id=body.workspace_id,
            )
    return _response.success(SecretMeta(**secret).model_dump())


@router.post("/{key}/rotate", status_code=200)
async def rotate_secret_route(
    request: Request,
    key: str,
    body: SecretRotate,
    scope: str = "global",
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> dict:
    vault = _ensure_vault_available(request)
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, vault, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            secret = await _service.rotate_secret(
                pool, conn, ctx,
                vault_client=vault,
                key=key,
                value=body.value,
                description=body.description,
                scope=scope,
                org_id=org_id,
                workspace_id=workspace_id,
            )
    return _response.success(SecretMeta(**secret).model_dump())


@router.delete("/{key}", status_code=204)
async def delete_secret_route(
    request: Request,
    key: str,
    scope: str = "global",
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> Response:
    vault = _ensure_vault_available(request)
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, vault, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_secret(
                pool, conn, ctx,
                vault_client=vault,
                key=key,
                scope=scope, org_id=org_id, workspace_id=workspace_id,
            )
    return Response(status_code=204)

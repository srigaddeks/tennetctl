"""
vault.configs — FastAPI routes. Standard 5-endpoint shape under /v1/vault-configs.
Configs are plaintext + viewable + editable. Value is carried in every response.
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
    "backend.02_features.02_vault.sub_features.02_configs.schemas"
)
_service: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.service"
)

ConfigCreate = _schemas.ConfigCreate
ConfigUpdate = _schemas.ConfigUpdate
ConfigMeta = _schemas.ConfigMeta

router = APIRouter(prefix="/v1/vault-configs", tags=["vault.configs"])


def _ensure_vault_available(request: Request) -> None:
    config = request.app.state.config
    if not config.allow_unauthenticated_vault:
        raise _errors.AppError(
            code="VAULT_LOCKED",
            message="Vault routes are locked. Set TENNETCTL_ALLOW_UNAUTHENTICATED_VAULT=true.",
            status_code=503,
        )


def _build_ctx(request: Request, pool: Any, *, audit_category: str) -> Any:
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=getattr(state, "org_id", None) or request.headers.get("x-org-id"),
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        application_id=getattr(state, "application_id", None) or request.headers.get("x-application-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category=audit_category,
        pool=pool,
        extras={"pool": pool},
    )


@router.get("", status_code=200)
async def list_configs_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    scope: str | None = None,
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> dict:
    _ensure_vault_available(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_configs(
            conn, ctx,
            limit=limit, offset=offset,
            scope=scope, org_id=org_id, workspace_id=workspace_id,
        )
    data = [ConfigMeta(**row).model_dump() for row in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_config_route(request: Request, body: ConfigCreate) -> dict:
    _ensure_vault_available(request)
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            config = await _service.create_config(
                pool, conn, ctx,
                key=body.key,
                value_type=body.value_type,
                value=body.value,
                description=body.description,
                scope=body.scope,
                org_id=body.org_id,
                workspace_id=body.workspace_id,
            )
    return _response.success(ConfigMeta(**config).model_dump())


@router.get("/{config_id}", status_code=200)
async def get_config_route(request: Request, config_id: str) -> dict:
    _ensure_vault_available(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        config = await _service.get_config(conn, ctx, config_id=config_id)
    if config is None or config.get("deleted_at") is not None:
        raise _errors.NotFoundError(f"vault config {config_id!r} not found")
    return _response.success(ConfigMeta(**config).model_dump())


@router.patch("/{config_id}", status_code=200)
async def update_config_route(
    request: Request,
    config_id: str,
    body: ConfigUpdate,
) -> dict:
    _ensure_vault_available(request)
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")

    # Distinguish "field omitted" from "field explicitly null".
    payload = body.model_dump(exclude_unset=True)
    has_value = "value" in payload
    has_description = "description" in payload
    has_is_active = "is_active" in payload

    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            config = await _service.update_config(
                pool, conn, ctx,
                config_id=config_id,
                value=body.value,
                description=body.description,
                is_active=body.is_active,
                has_value=has_value,
                has_description=has_description,
                has_is_active=has_is_active,
            )
    return _response.success(ConfigMeta(**config).model_dump())


@router.delete("/{config_id}", status_code=204)
async def delete_config_route(request: Request, config_id: str) -> Response:
    _ensure_vault_available(request)
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_config(pool, conn, ctx, config_id=config_id)
    return Response(status_code=204)

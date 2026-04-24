"""iam.roles — FastAPI routes (5-endpoint shape)."""

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
    "backend.02_features.03_iam.sub_features.04_roles.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.04_roles.service"
)

RoleCreate = _schemas.RoleCreate
RoleUpdate = _schemas.RoleUpdate
RoleRead = _schemas.RoleRead

router = APIRouter(prefix="/v1/roles", tags=["iam.roles"])


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
async def list_roles_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    org_id: str | None = None,
    role_type: str | None = None,
    is_active: bool | None = None,
    application_id: str | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_roles(
            conn, ctx,
            limit=limit, offset=offset,
            org_id=org_id, role_type=role_type, is_active=is_active,
            application_id=application_id,
        )
    data = [RoleRead(**r).model_dump() for r in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_role_route(request: Request, body: RoleCreate) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            role = await _service.create_role(
                pool, conn, ctx,
                org_id=body.org_id,
                application_id=body.application_id,
                role_type=body.role_type,
                code=body.code,
                label=body.label,
                description=body.description,
            )
    return _response.success(RoleRead(**role).model_dump())


@router.get("/{role_id}", status_code=200)
async def get_role_route(request: Request, role_id: str) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        role = await _service.get_role(conn, ctx, role_id=role_id)
    if role is None:
        raise _errors.NotFoundError(f"Role {role_id!r} not found.")
    return _response.success(RoleRead(**role).model_dump())


@router.patch("/{role_id}", status_code=200)
async def update_role_route(request: Request, role_id: str, body: RoleUpdate) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            role = await _service.update_role(
                pool, conn, ctx,
                role_id=role_id,
                label=body.label,
                description=body.description,
                is_active=body.is_active,
            )
    return _response.success(RoleRead(**role).model_dump())


@router.delete("/{role_id}", status_code=204)
async def delete_role_route(request: Request, role_id: str) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_role(pool, conn, ctx, role_id=role_id)
    return Response(status_code=204)

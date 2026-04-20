"""featureflags.permissions — FastAPI routes.

/v1/flag-permissions:
  GET          — list, filter by role_id / flag_id / permission
  POST         — grant a permission
  GET /{id}    — get one
  DELETE /{id} — revoke

No PATCH — permissions are immutable (you revoke and re-grant with a different permission).
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
    "backend.02_features.09_featureflags.sub_features.02_permissions.schemas"
)
_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.02_permissions.service"
)

RoleFlagPermissionCreate = _schemas.RoleFlagPermissionCreate
RoleFlagPermissionRead = _schemas.RoleFlagPermissionRead

router = APIRouter(prefix="/v1/flag-permissions", tags=["featureflags.permissions"])


def _build_ctx(request: Request, pool: Any, *, audit_category: str) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=request.headers.get("x-user-id"),
        session_id=request.headers.get("x-session-id"),
        org_id=request.headers.get("x-org-id"),
        workspace_id=request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category=audit_category,
        pool=pool,
        extras={"pool": pool},
    )


@router.get("", status_code=200)
async def list_grants_route(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    role_id: str | None = None,
    flag_id: str | None = None,
    permission: str | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_grants(
            conn, ctx,
            limit=limit, offset=offset,
            role_id=role_id, flag_id=flag_id, permission=permission,
        )
    data = [RoleFlagPermissionRead(**r).model_dump() for r in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_grant_route(
    request: Request, body: RoleFlagPermissionCreate,
) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            grant = await _service.grant_permission(
                pool, conn, ctx,
                role_id=body.role_id,
                flag_id=body.flag_id,
                permission=body.permission,
            )
    return _response.success(RoleFlagPermissionRead(**grant).model_dump())


@router.get("/{grant_id}", status_code=200)
async def get_grant_route(request: Request, grant_id: str) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        g = await _service.get_grant(conn, ctx, grant_id=grant_id)
    if g is None:
        raise _errors.NotFoundError(f"Grant {grant_id!r} not found.")
    return _response.success(RoleFlagPermissionRead(**g).model_dump())


@router.delete("/{grant_id}", status_code=204)
async def delete_grant_route(request: Request, grant_id: str) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.revoke_permission(pool, conn, ctx, grant_id=grant_id)
    return Response(status_code=204)

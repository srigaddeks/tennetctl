"""
iam.users — FastAPI routes (5-endpoint shape).
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
    "backend.02_features.03_iam.sub_features.03_users.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)

UserCreate = _schemas.UserCreate
UserUpdate = _schemas.UserUpdate
UserRead = _schemas.UserRead

router = APIRouter(prefix="/v1/users", tags=["iam.users"])


def _build_ctx(request: Request, pool: Any, *, audit_category: str) -> Any:
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=getattr(state, "org_id", None) or request.headers.get("x-org-id"),
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category=audit_category,
        pool=pool,
        extras={"pool": pool},
    )


@router.get("", status_code=200)
async def list_users_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    account_type: str | None = None,
    is_active: bool | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_users(
            conn, ctx,
            limit=limit, offset=offset,
            account_type=account_type, is_active=is_active,
        )
    data = [UserRead(**row).model_dump() for row in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_user_route(request: Request, body: UserCreate) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            user = await _service.create_user(
                pool, conn, ctx,
                account_type=body.account_type,
                email=body.email,
                display_name=body.display_name,
                avatar_url=body.avatar_url,
            )
    return _response.success(UserRead(**user).model_dump())


@router.get("/{user_id}", status_code=200)
async def get_user_route(request: Request, user_id: str) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        user = await _service.get_user(conn, ctx, user_id=user_id)
    if user is None:
        raise _errors.NotFoundError(f"User {user_id!r} not found.")
    return _response.success(UserRead(**user).model_dump())


@router.patch("/{user_id}", status_code=200)
async def update_user_route(
    request: Request, user_id: str, body: UserUpdate,
) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            user = await _service.update_user(
                pool, conn, ctx,
                user_id=user_id,
                email=body.email,
                display_name=body.display_name,
                avatar_url=body.avatar_url,
                is_active=body.is_active,
                status=body.status,
            )
    return _response.success(UserRead(**user).model_dump())


@router.delete("/{user_id}", status_code=204)
async def delete_user_route(request: Request, user_id: str) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_user(pool, conn, ctx, user_id=user_id)
    return Response(status_code=204)

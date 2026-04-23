"""
iam.workspaces — FastAPI routes (5-endpoint shape).

Mirrors iam.orgs routes. org_id is accepted as a query filter on list, as a
required body field on create, and is frozen on PATCH (no cross-org moves in v1).
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
    "backend.02_features.03_iam.sub_features.02_workspaces.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.02_workspaces.service"
)

WorkspaceCreate = _schemas.WorkspaceCreate
WorkspaceUpdate = _schemas.WorkspaceUpdate
WorkspaceRead = _schemas.WorkspaceRead

router = APIRouter(prefix="/v1/workspaces", tags=["iam.workspaces"])


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
async def list_workspaces_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    org_id: str | None = None,
    is_active: bool | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_workspaces(
            conn,
            ctx,
            limit=limit,
            offset=offset,
            org_id=org_id,
            is_active=is_active,
        )
    data = [WorkspaceRead(**row).model_dump() for row in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_workspace_route(
    request: Request,
    body: WorkspaceCreate,
) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            ws = await _service.create_workspace(
                pool,
                conn,
                ctx,
                org_id=body.org_id,
                slug=body.slug,
                display_name=body.display_name,
            )
    return _response.success(WorkspaceRead(**ws).model_dump())


@router.get("/{workspace_id}", status_code=200)
async def get_workspace_route(request: Request, workspace_id: str) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        ws = await _service.get_workspace(conn, ctx, workspace_id=workspace_id)
    if ws is None:
        raise _errors.NotFoundError(f"Workspace {workspace_id!r} not found.")
    return _response.success(WorkspaceRead(**ws).model_dump())


@router.patch("/{workspace_id}", status_code=200)
async def update_workspace_route(
    request: Request,
    workspace_id: str,
    body: WorkspaceUpdate,
) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            ws = await _service.update_workspace(
                pool,
                conn,
                ctx,
                workspace_id=workspace_id,
                slug=body.slug,
                display_name=body.display_name,
            )
    return _response.success(WorkspaceRead(**ws).model_dump())


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace_route(request: Request, workspace_id: str) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_workspace(pool, conn, ctx, workspace_id=workspace_id)
    return Response(status_code=204)

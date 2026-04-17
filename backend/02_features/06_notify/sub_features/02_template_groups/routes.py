"""Routes for notify.template_groups."""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_errors: Any = import_module("backend.01_core.errors")
_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_schemas: Any = import_module(
    "backend.02_features.06_notify.sub_features.02_template_groups.schemas"
)
_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.02_template_groups.service"
)

TemplateGroupCreate = _schemas.TemplateGroupCreate
TemplateGroupUpdate = _schemas.TemplateGroupUpdate
TemplateGroupRow = _schemas.TemplateGroupRow

router = APIRouter(tags=["notify.template_groups"])


def _build_ctx(request: Request, pool: Any, *, audit_category: str = "setup") -> Any:
    """Template group mutations are org-level config (no workspace scope);
    audit_category='setup' bypasses the workspace_id requirement in chk_evt_audit_scope.
    """
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=getattr(state, "org_id", None) or request.headers.get("x-org-id"),
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", None) or _core_id.uuid7(),
        audit_category=audit_category,
        extras={"pool": pool},
    )


@router.get("/v1/notify/template-groups", status_code=200)
async def list_template_groups_route(request: Request, org_id: str) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items = await _service.list_template_groups(conn, org_id=org_id)
    data = [TemplateGroupRow(**r).model_dump() for r in items]
    return _response.success({"items": data, "total": len(data)})


@router.post("/v1/notify/template-groups", status_code=201)
async def create_template_group_route(request: Request, body: TemplateGroupCreate) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        row = await _service.create_template_group(conn, pool, ctx2, data=body.model_dump())
    return _response.success(TemplateGroupRow(**row).model_dump())


@router.get("/v1/notify/template-groups/{group_id}", status_code=200)
async def get_template_group_route(request: Request, group_id: str) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_template_group(conn, group_id=group_id)
    if row is None:
        raise _errors.NotFoundError(f"template group {group_id!r} not found")
    return _response.success(TemplateGroupRow(**row).model_dump())


@router.patch("/v1/notify/template-groups/{group_id}", status_code=200)
async def update_template_group_route(
    request: Request, group_id: str, body: TemplateGroupUpdate
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        row = await _service.update_template_group(
            conn, pool, ctx2, group_id=group_id,
            data=body.model_dump(exclude_none=True),
        )
    if row is None:
        raise _errors.NotFoundError(f"template group {group_id!r} not found")
    return _response.success(TemplateGroupRow(**row).model_dump())


@router.delete("/v1/notify/template-groups/{group_id}", status_code=204)
async def delete_template_group_route(request: Request, group_id: str) -> None:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        deleted = await _service.delete_template_group(conn, pool, ctx2, group_id=group_id)
    if not deleted:
        raise _errors.NotFoundError(f"template group {group_id!r} not found")

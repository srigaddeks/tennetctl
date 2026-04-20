"""Routes for notify.template_variables — nested under /v1/notify/templates/{template_id}/variables."""

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
    "backend.02_features.06_notify.sub_features.04_variables.schemas"
)
_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.04_variables.service"
)

TemplateVariableCreate = _schemas.TemplateVariableCreate
TemplateVariableUpdate = _schemas.TemplateVariableUpdate
TemplateVariableRow = _schemas.TemplateVariableRow
ResolveRequest = _schemas.ResolveRequest

router = APIRouter(tags=["notify.template_variables"])


def _build_ctx(request: Request, pool: Any) -> Any:
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=getattr(state, "org_id", None) or request.headers.get("x-org-id"),
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", None) or _core_id.uuid7(),
        audit_category="setup",
        pool=pool,
        extras={"pool": pool},
    )


@router.get("/{template_id}/variables", status_code=200)
async def list_variables_route(request: Request, template_id: str) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items = await _service.list_variables(conn, template_id=template_id)
    data = [TemplateVariableRow(**r).model_dump() for r in items]
    return _response.success({"items": data, "total": len(data)})


@router.post("/{template_id}/variables", status_code=201)
async def create_variable_route(
    request: Request, template_id: str, body: TemplateVariableCreate
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        row = await _service.create_variable(
            conn, pool, ctx2,
            template_id=template_id,
            data=body.model_dump(),
        )
    return _response.success(TemplateVariableRow(**row).model_dump())


# IMPORTANT: /resolve must be declared before /{var_id} to avoid FastAPI
# routing "resolve" as a var_id path parameter.
@router.post("/{template_id}/variables/resolve", status_code=200)
async def resolve_variables_route(
    request: Request, template_id: str, body: ResolveRequest
) -> dict:
    """Resolve all registered variables for a template with the given context. For preview/testing."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        resolved = await _service.resolve_variables(
            conn, template_id=template_id, context=body.context
        )
    return _response.success({"resolved": resolved})


@router.get("/{template_id}/variables/{var_id}", status_code=200)
async def get_variable_route(request: Request, template_id: str, var_id: str) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_variable(conn, var_id=var_id)
    if row is None or row.get("template_id") != template_id:
        raise _errors.NotFoundError(f"variable {var_id!r} not found")
    return _response.success(TemplateVariableRow(**row).model_dump())


@router.patch("/{template_id}/variables/{var_id}", status_code=200)
async def update_variable_route(
    request: Request, template_id: str, var_id: str, body: TemplateVariableUpdate
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        row = await _service.update_variable(
            conn, pool, ctx2,
            var_id=var_id,
            data=body.model_dump(exclude_none=True),
        )
    if row is None or row.get("template_id") != template_id:
        raise _errors.NotFoundError(f"variable {var_id!r} not found")
    return _response.success(TemplateVariableRow(**row).model_dump())


@router.delete("/{template_id}/variables/{var_id}", status_code=204)
async def delete_variable_route(
    request: Request, template_id: str, var_id: str
) -> None:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        deleted = await _service.delete_variable(conn, pool, ctx2, var_id=var_id)
    if not deleted:
        raise _errors.NotFoundError(f"variable {var_id!r} not found")

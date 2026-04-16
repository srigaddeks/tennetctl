"""iam.applications — FastAPI routes."""

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
    "backend.02_features.03_iam.sub_features.06_applications.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.06_applications.service"
)

ApplicationCreate = _schemas.ApplicationCreate
ApplicationUpdate = _schemas.ApplicationUpdate
ApplicationRead = _schemas.ApplicationRead

router = APIRouter(prefix="/v1/applications", tags=["iam.applications"])


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
        extras={"pool": pool},
    )


@router.get("", status_code=200)
async def list_applications_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    org_id: str | None = None,
    is_active: bool | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_applications(
            conn, ctx, limit=limit, offset=offset, org_id=org_id, is_active=is_active,
        )
    data = [ApplicationRead(**r).model_dump() for r in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_application_route(request: Request, body: ApplicationCreate) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            a = await _service.create_application(
                pool, conn, ctx,
                org_id=body.org_id,
                code=body.code,
                label=body.label,
                description=body.description,
            )
    return _response.success(ApplicationRead(**a).model_dump())


@router.get("/{application_id}", status_code=200)
async def get_application_route(request: Request, application_id: str) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        a = await _service.get_application(conn, ctx, application_id=application_id)
    if a is None:
        raise _errors.NotFoundError(f"Application {application_id!r} not found.")
    return _response.success(ApplicationRead(**a).model_dump())


@router.patch("/{application_id}", status_code=200)
async def update_application_route(
    request: Request, application_id: str, body: ApplicationUpdate,
) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            a = await _service.update_application(
                pool, conn, ctx,
                application_id=application_id,
                label=body.label,
                description=body.description,
                is_active=body.is_active,
            )
    return _response.success(ApplicationRead(**a).model_dump())


@router.delete("/{application_id}", status_code=204)
async def delete_application_route(request: Request, application_id: str) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_application(pool, conn, ctx, application_id=application_id)
    return Response(status_code=204)

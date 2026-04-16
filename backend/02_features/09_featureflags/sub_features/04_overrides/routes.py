"""featureflags.overrides — FastAPI routes."""
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
    "backend.02_features.09_featureflags.sub_features.04_overrides.schemas"
)
_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.04_overrides.service"
)

OverrideCreate = _schemas.OverrideCreate
OverrideUpdate = _schemas.OverrideUpdate
OverrideRead = _schemas.OverrideRead

router = APIRouter(prefix="/v1/flag-overrides", tags=["featureflags.overrides"])


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
async def list_overrides_route(
    request: Request,
    limit: int = 100, offset: int = 0,
    flag_id: str | None = None,
    environment: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    is_active: bool | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_overrides(
            conn, ctx, limit=limit, offset=offset,
            flag_id=flag_id, environment=environment,
            entity_type=entity_type, entity_id=entity_id,
            is_active=is_active,
        )
    data = [OverrideRead(**o).model_dump() for o in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_override_route(request: Request, body: OverrideCreate) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            o = await _service.create_override(
                pool, conn, ctx,
                flag_id=body.flag_id,
                environment=body.environment,
                entity_type=body.entity_type,
                entity_id=body.entity_id,
                value=body.value,
                reason=body.reason,
            )
    return _response.success(OverrideRead(**o).model_dump())


@router.get("/{override_id}", status_code=200)
async def get_override_route(request: Request, override_id: str) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        o = await _service.get_override(conn, ctx, override_id=override_id)
    if o is None:
        raise _errors.NotFoundError(f"Override {override_id!r} not found.")
    return _response.success(OverrideRead(**o).model_dump())


@router.patch("/{override_id}", status_code=200)
async def update_override_route(
    request: Request, override_id: str, body: OverrideUpdate,
) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            kw: dict[str, Any] = {}
            if body.value is not None:
                kw["value"] = body.value
            if body.reason is not None:
                kw["reason"] = body.reason
            if body.is_active is not None:
                kw["is_active"] = body.is_active
            o = await _service.update_override(
                pool, conn, ctx, override_id=override_id, **kw,
            )
    return _response.success(OverrideRead(**o).model_dump())


@router.delete("/{override_id}", status_code=204)
async def delete_override_route(request: Request, override_id: str) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_override(pool, conn, ctx, override_id=override_id)
    return Response(status_code=204)

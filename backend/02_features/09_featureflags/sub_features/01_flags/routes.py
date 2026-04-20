"""
featureflags.flags — FastAPI routes.

Two resources:
- /v1/flags — CRUD (5 endpoints, 5-endpoint shape)
- /v1/flag-states — list / get / patch (3 endpoints; POST is auto on flag create, DELETE is cascade)
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
    "backend.02_features.09_featureflags.sub_features.01_flags.schemas"
)
_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.01_flags.service"
)

FlagCreate = _schemas.FlagCreate
FlagUpdate = _schemas.FlagUpdate
FlagRead = _schemas.FlagRead
FlagStateRead = _schemas.FlagStateRead
FlagStateUpdate = _schemas.FlagStateUpdate


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


# ─── Flag router ─────────────────────────────────────────────────────

flag_router = APIRouter(prefix="/v1/flags", tags=["featureflags.flags"])


@flag_router.get("", status_code=200)
async def list_flags_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    scope: str | None = None,
    org_id: str | None = None,
    application_id: str | None = None,
    is_active: bool | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_flags(
            conn, ctx,
            limit=limit, offset=offset,
            scope=scope, org_id=org_id, application_id=application_id,
            is_active=is_active,
        )
    data = [FlagRead(**row).model_dump() for row in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@flag_router.post("", status_code=201)
async def create_flag_route(request: Request, body: FlagCreate) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            flag = await _service.create_flag(
                pool, conn, ctx,
                scope=body.scope,
                org_id=body.org_id,
                application_id=body.application_id,
                flag_key=body.flag_key,
                value_type=body.value_type,
                default_value=body.default_value,
                description=body.description,
            )
    return _response.success(FlagRead(**flag).model_dump())


@flag_router.get("/{flag_id}", status_code=200)
async def get_flag_route(request: Request, flag_id: str) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        flag = await _service.get_flag(conn, ctx, flag_id=flag_id)
    if flag is None:
        raise _errors.NotFoundError(f"Flag {flag_id!r} not found.")
    return _response.success(FlagRead(**flag).model_dump())


@flag_router.patch("/{flag_id}", status_code=200)
async def update_flag_route(
    request: Request, flag_id: str, body: FlagUpdate,
) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            kw: dict[str, Any] = {}
            if body.default_value is not None:
                kw["default_value"] = body.default_value
            if body.description is not None:
                kw["description"] = body.description
            if body.is_active is not None:
                kw["is_active"] = body.is_active
            flag = await _service.update_flag(
                pool, conn, ctx, flag_id=flag_id, **kw,
            )
    return _response.success(FlagRead(**flag).model_dump())


@flag_router.delete("/{flag_id}", status_code=204)
async def delete_flag_route(request: Request, flag_id: str) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_flag(pool, conn, ctx, flag_id=flag_id)
    return Response(status_code=204)


# ─── Flag-state router ───────────────────────────────────────────────

state_router = APIRouter(prefix="/v1/flag-states", tags=["featureflags.flag-states"])


@state_router.get("", status_code=200)
async def list_flag_states_route(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    flag_id: str | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_flag_states(
            conn, ctx, limit=limit, offset=offset, flag_id=flag_id,
        )
    data = [FlagStateRead(**row).model_dump() for row in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@state_router.get("/{state_id}", status_code=200)
async def get_flag_state_route(request: Request, state_id: str) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        st = await _service.get_flag_state(conn, ctx, state_id=state_id)
    if st is None:
        raise _errors.NotFoundError(f"Flag state {state_id!r} not found.")
    return _response.success(FlagStateRead(**st).model_dump())


@state_router.patch("/{state_id}", status_code=200)
async def update_flag_state_route(
    request: Request, state_id: str, body: FlagStateUpdate,
) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            kw: dict[str, Any] = {}
            if body.is_enabled is not None:
                kw["is_enabled"] = body.is_enabled
            if body.env_default_value is not None:
                kw["env_default_value"] = body.env_default_value
            st = await _service.update_flag_state(
                pool, conn, ctx, state_id=state_id, **kw,
            )
    return _response.success(FlagStateRead(**st).model_dump())


# ─── Combined router ─────────────────────────────────────────────────

router = APIRouter()
router.include_router(flag_router)
router.include_router(state_router)

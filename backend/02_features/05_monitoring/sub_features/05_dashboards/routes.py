"""Routes for monitoring.dashboards — CRUD + panels."""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request, Response

_errors: Any = import_module("backend.01_core.errors")
_resp: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.05_dashboards.schemas"
)
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.05_dashboards.service"
)

DashboardCreateRequest = _schemas.DashboardCreateRequest
DashboardUpdateRequest = _schemas.DashboardUpdateRequest
DashboardResponse = _schemas.DashboardResponse
DashboardDetailResponse = _schemas.DashboardDetailResponse
PanelCreateRequest = _schemas.PanelCreateRequest
PanelUpdateRequest = _schemas.PanelUpdateRequest
PanelResponse = _schemas.PanelResponse

router = APIRouter(tags=["monitoring.dashboards"])


def _scope(request: Request) -> tuple[str, str]:
    state = request.state
    org_id = getattr(state, "org_id", None) or request.headers.get("x-org-id")
    user_id = getattr(state, "user_id", None) or request.headers.get("x-user-id")
    if not org_id:
        raise _errors.AppError("UNAUTHORIZED", "org_id required", 401)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "user_id required", 401)
    return org_id, user_id


def _build_ctx(request: Request) -> Any:
    org_id, user_id = _scope(request)
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=user_id,
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=org_id,
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        application_id=getattr(state, "application_id", None) or request.headers.get("x-application-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", "") or _core_id.uuid7(),
        audit_category="user",
    )


# ---------- dashboards ----------

@router.post("/v1/monitoring/dashboards", status_code=201)
async def create_dashboard_route(
    request: Request, body: DashboardCreateRequest,
) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.create_dashboard(
            conn, ctx, pool,
            org_id=org_id, owner_user_id=user_id,
            name=body.name, description=body.description,
            layout=body.layout, shared=body.shared,
        )
    return _resp.success(DashboardResponse.from_row(row).model_dump())


@router.get("/v1/monitoring/dashboards", status_code=200)
async def list_dashboards_route(request: Request) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    async with pool.acquire() as conn:
        rows = await _service.list_dashboards(
            conn, org_id=org_id, owner_user_id=user_id,
        )
    items = [DashboardResponse.from_row(r).model_dump() for r in rows]
    return _resp.success({"items": items, "total": len(items)})


@router.get("/v1/monitoring/dashboards/{id}", status_code=200)
async def get_dashboard_route(request: Request, id: str) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    async with pool.acquire() as conn:
        row = await _service.get_dashboard(
            conn, org_id=org_id, user_id=user_id, id=id,
        )
        if row is None:
            raise _errors.NotFoundError(f"dashboard {id!r} not found")
        panels = await _service.list_panels(
            conn, org_id=org_id, user_id=user_id, dashboard_id=id,
        ) or []
    base = DashboardResponse.from_row(row).model_dump()
    base["panels"] = [PanelResponse.from_row(p).model_dump() for p in panels]
    return _resp.success(base)


@router.patch("/v1/monitoring/dashboards/{id}", status_code=200)
async def update_dashboard_route(
    request: Request, id: str, body: DashboardUpdateRequest,
) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.update_dashboard(
            conn, ctx, pool,
            org_id=org_id, user_id=user_id, id=id,
            name=body.name, description=body.description,
            layout=body.layout, shared=body.shared, is_active=body.is_active,
        )
    if row is None:
        raise _errors.NotFoundError(f"dashboard {id!r} not found")
    return _resp.success(DashboardResponse.from_row(row).model_dump())


@router.delete(
    "/v1/monitoring/dashboards/{id}",
    status_code=204,
    response_class=Response,
)
async def delete_dashboard_route(request: Request, id: str) -> Response:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        ok = await _service.delete_dashboard(
            conn, ctx, pool, org_id=org_id, user_id=user_id, id=id,
        )
    if not ok:
        raise _errors.NotFoundError(f"dashboard {id!r} not found")
    return Response(status_code=204)


# ---------- panels ----------

@router.get("/v1/monitoring/dashboards/{id}/panels", status_code=200)
async def list_panels_route(request: Request, id: str) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    async with pool.acquire() as conn:
        rows = await _service.list_panels(
            conn, org_id=org_id, user_id=user_id, dashboard_id=id,
        )
    if rows is None:
        raise _errors.NotFoundError(f"dashboard {id!r} not found")
    items = [PanelResponse.from_row(r).model_dump() for r in rows]
    return _resp.success({"items": items, "total": len(items)})


@router.post("/v1/monitoring/dashboards/{id}/panels", status_code=201)
async def create_panel_route(
    request: Request, id: str, body: PanelCreateRequest,
) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.create_panel(
            conn, ctx, pool,
            org_id=org_id, user_id=user_id, dashboard_id=id,
            title=body.title, panel_type=body.panel_type,
            dsl=body.dsl,
            grid_pos=body.grid_pos.model_dump() if body.grid_pos else None,
            display_opts=body.display_opts,
        )
    if row is None:
        raise _errors.NotFoundError(f"dashboard {id!r} not found")
    return _resp.success(PanelResponse.from_row(row).model_dump())


@router.get(
    "/v1/monitoring/dashboards/{id}/panels/{panel_id}",
    status_code=200,
)
async def get_panel_route(request: Request, id: str, panel_id: str) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    async with pool.acquire() as conn:
        row = await _service.get_panel(
            conn, org_id=org_id, user_id=user_id,
            dashboard_id=id, panel_id=panel_id,
        )
    if row is None:
        raise _errors.NotFoundError(f"panel {panel_id!r} not found")
    return _resp.success(PanelResponse.from_row(row).model_dump())


@router.patch(
    "/v1/monitoring/dashboards/{id}/panels/{panel_id}",
    status_code=200,
)
async def update_panel_route(
    request: Request, id: str, panel_id: str, body: PanelUpdateRequest,
) -> dict:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        row = await _service.update_panel(
            conn, ctx, pool,
            org_id=org_id, user_id=user_id,
            dashboard_id=id, panel_id=panel_id,
            title=body.title, panel_type=body.panel_type,
            dsl=body.dsl,
            grid_pos=body.grid_pos.model_dump() if body.grid_pos else None,
            display_opts=body.display_opts,
        )
    if row is None:
        raise _errors.NotFoundError(f"panel {panel_id!r} not found")
    return _resp.success(PanelResponse.from_row(row).model_dump())


@router.delete(
    "/v1/monitoring/dashboards/{id}/panels/{panel_id}",
    status_code=204,
    response_class=Response,
)
async def delete_panel_route(
    request: Request, id: str, panel_id: str,
) -> Response:
    pool = request.app.state.pool
    org_id, user_id = _scope(request)
    ctx_base = _build_ctx(request)
    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        ok = await _service.delete_panel(
            conn, ctx, pool,
            org_id=org_id, user_id=user_id,
            dashboard_id=id, panel_id=panel_id,
        )
    if not ok:
        raise _errors.NotFoundError(f"panel {panel_id!r} not found")
    return Response(status_code=204)

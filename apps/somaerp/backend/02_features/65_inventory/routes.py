"""Inventory routes — /v1/somaerp/inventory/*."""

from __future__ import annotations

from datetime import datetime
from importlib import import_module

from fastapi import APIRouter, Query, Request

_service = import_module(
    "apps.somaerp.backend.02_features.65_inventory.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.65_inventory.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")


router = APIRouter(
    prefix="/v1/somaerp/inventory",
    tags=["inventory"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


def _parse_ts(val: str | None) -> datetime | None:
    if val is None or val == "":
        return None
    try:
        return datetime.fromisoformat(val)
    except ValueError as e:
        raise _errors.ValidationError(
            f"Invalid ISO timestamp: {val}",
            code="INVALID_TIMESTAMP",
        ) from e


# ── Current inventory ───────────────────────────────────────────────────


@router.get("/current")
async def list_current(
    request: Request,
    kitchen_id: str | None = Query(default=None),
    raw_material_id: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_current(
            conn,
            tenant_id=workspace_id,
            kitchen_id=kitchen_id,
            raw_material_id=raw_material_id,
            category_id=category_id,
            limit=limit,
            offset=offset,
        )
    data = [
        _schemas.InventoryCurrentOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


# ── Movements ───────────────────────────────────────────────────────────


@router.get("/movements")
async def list_movements(
    request: Request,
    kitchen_id: str | None = Query(default=None),
    raw_material_id: str | None = Query(default=None),
    movement_type: str | None = Query(default=None),
    ts_after: str | None = Query(default=None),
    ts_before: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_movements(
            conn,
            tenant_id=workspace_id,
            kitchen_id=kitchen_id,
            raw_material_id=raw_material_id,
            movement_type=movement_type,
            ts_after=_parse_ts(ts_after),
            ts_before=_parse_ts(ts_before),
            limit=limit,
            offset=offset,
        )
    data = [
        _schemas.InventoryMovementOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


@router.post("/movements", status_code=201)
async def record_movement(
    request: Request,
    payload: _schemas.InventoryMovementCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.record_movement(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(
        _schemas.InventoryMovementOut(**row).model_dump(mode="json"),
    )


# ── MRP-lite planner ────────────────────────────────────────────────────


@router.post("/plan")
async def compute_plan(
    request: Request,
    payload: _schemas.ProcurementPlanRequest,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        result = await _service.compute_plan(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            kitchen_id=payload.kitchen_id,
            demand=[d.model_dump(mode="python") for d in payload.demand],
        )
    return _response.ok(
        _schemas.ProcurementPlanResponse(**result).model_dump(mode="json"),
    )

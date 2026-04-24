"""Delivery runs routes — /v1/somaerp/delivery/runs + /stops + /board."""

from __future__ import annotations

from datetime import date
from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.95_delivery_runs.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.95_delivery_runs.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")


router = APIRouter(
    prefix="/v1/somaerp/delivery",
    tags=["delivery", "runs"],
)


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


def _parse_date(val: str | None) -> date | None:
    if val is None or val == "":
        return None
    try:
        return date.fromisoformat(val)
    except ValueError as e:
        raise _errors.ValidationError(
            f"Invalid ISO date: {val}", code="INVALID_DATE",
        ) from e


# ── Runs CRUD ────────────────────────────────────────────────────────


@router.get("/runs")
async def list_runs(
    request: Request,
    route_id: str | None = Query(default=None),
    rider_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    run_date_from: str | None = Query(default=None),
    run_date_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_runs(
            conn,
            tenant_id=workspace_id,
            route_id=route_id,
            rider_id=rider_id,
            status=status,
            run_date_from=_parse_date(run_date_from),
            run_date_to=_parse_date(run_date_to),
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.RunOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/runs", status_code=201)
async def create_run(
    request: Request, payload: _schemas.RunCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_run(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(_schemas.RunOut(**row).model_dump(mode="json"))


@router.get("/runs/{run_id}")
async def get_run(request: Request, run_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        detail = await _service.get_run_detail(
            conn, tenant_id=workspace_id, run_id=run_id,
        )
    run_out = _schemas.RunOut(**detail["run"]).model_dump(mode="json")
    stops_out = [
        _schemas.StopOut(**s).model_dump(mode="json") for s in detail["stops"]
    ]
    return _response.ok({"run": run_out, "stops": stops_out})


@router.patch("/runs/{run_id}")
async def patch_run(
    request: Request, run_id: str, payload: _schemas.RunUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.patch_run(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            run_id=run_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.RunOut(**row).model_dump(mode="json"))


@router.delete(
    "/runs/{run_id}", status_code=204, response_class=Response,
)
async def delete_run(request: Request, run_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_run(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            run_id=run_id,
        )
    return Response(status_code=204)


# ── Generate stops ────────────────────────────────────────────────────


@router.post("/runs/{run_id}/generate-stops", status_code=201)
async def generate_run_stops(request: Request, run_id: str) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        result = await _service.generate_stops(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            run_id=run_id,
        )
    run_out = _schemas.RunOut(**result["run"]).model_dump(mode="json")
    stops_out = [
        _schemas.StopOut(**s).model_dump(mode="json") for s in result["stops"]
    ]
    return _response.ok(
        {"run": run_out, "stops": stops_out, "count": result["count"]},
    )


# ── Stops ────────────────────────────────────────────────────────────


@router.get("/runs/{run_id}/stops")
async def list_run_stops(request: Request, run_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_stops(
            conn, tenant_id=workspace_id, run_id=run_id,
        )
    data = [_schemas.StopOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.patch("/runs/{run_id}/stops/{stop_id}")
async def patch_run_stop(
    request: Request,
    run_id: str,
    stop_id: str,
    payload: _schemas.StopUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.patch_stop(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            run_id=run_id,
            stop_id=stop_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.StopOut(**row).model_dump(mode="json"))


# ── Board ────────────────────────────────────────────────────────────


@router.get("/board")
async def delivery_board(
    request: Request,
    on_date: str | None = Query(default=None, alias="date"),
) -> dict:
    workspace_id = _require_workspace(request)
    target_date = _parse_date(on_date) or date.today()
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        board = await _service.get_board(
            conn, tenant_id=workspace_id, on_date=target_date,
        )
    kitchens_out = []
    for k in board["kitchens"]:
        runs_out = [
            _schemas.RunOut(**r).model_dump(mode="json") for r in k["runs"]
        ]
        kitchens_out.append(
            {
                "kitchen_id": k["kitchen_id"],
                "kitchen_name": k.get("kitchen_name"),
                "runs": runs_out,
            }
        )
    return _response.ok(
        {"date": board["date"].isoformat(), "kitchens": kitchens_out},
    )

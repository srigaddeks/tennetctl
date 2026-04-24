"""Procurement routes — /v1/somaerp/procurement/*."""

from __future__ import annotations

from datetime import date
from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.60_procurement.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.60_procurement.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")


router = APIRouter(
    prefix="/v1/somaerp/procurement",
    tags=["procurement"],
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


# ── Runs ────────────────────────────────────────────────────────────────


@router.get("/runs")
async def list_runs(
    request: Request,
    kitchen_id: str | None = Query(default=None),
    supplier_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    run_date_from: str | None = Query(default=None),
    run_date_to: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_runs(
            conn,
            tenant_id=workspace_id,
            kitchen_id=kitchen_id,
            supplier_id=supplier_id,
            status=status,
            run_date_from=_parse_date(run_date_from),
            run_date_to=_parse_date(run_date_to),
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [
        _schemas.ProcurementRunOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


@router.post("/runs", status_code=201)
async def create_run(
    request: Request, payload: _schemas.ProcurementRunCreate,
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
    return _response.ok(
        _schemas.ProcurementRunOut(**row).model_dump(mode="json"),
    )


@router.get("/runs/{run_id}")
async def get_run(request: Request, run_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_run(
            conn, tenant_id=workspace_id, run_id=run_id,
        )
    return _response.ok(
        _schemas.ProcurementRunOut(**row).model_dump(mode="json"),
    )


@router.patch("/runs/{run_id}")
async def patch_run(
    request: Request,
    run_id: str,
    payload: _schemas.ProcurementRunUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_run(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            run_id=run_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(
        _schemas.ProcurementRunOut(**row).model_dump(mode="json"),
    )


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


# ── Lines (nested) ──────────────────────────────────────────────────────


@router.get("/runs/{run_id}/lines")
async def list_lines(request: Request, run_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_lines(
            conn, tenant_id=workspace_id, run_id=run_id,
        )
    data = [
        _schemas.ProcurementLineOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


@router.post("/runs/{run_id}/lines", status_code=201)
async def add_line(
    request: Request,
    run_id: str,
    payload: _schemas.ProcurementLineCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.add_line(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            run_id=run_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(
        _schemas.ProcurementLineOut(**row).model_dump(mode="json"),
    )


@router.patch("/runs/{run_id}/lines/{line_id}")
async def patch_line(
    request: Request,
    run_id: str,
    line_id: str,
    payload: _schemas.ProcurementLineUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.patch_line(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            run_id=run_id,
            line_id=line_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(
        _schemas.ProcurementLineOut(**row).model_dump(mode="json"),
    )


@router.delete(
    "/runs/{run_id}/lines/{line_id}",
    status_code=204,
    response_class=Response,
)
async def delete_line(
    request: Request, run_id: str, line_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.delete_line(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            run_id=run_id,
            line_id=line_id,
        )
    return Response(status_code=204)

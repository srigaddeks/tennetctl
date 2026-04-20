"""Routes for monitoring.slos — CRUD + evaluations + budget snapshots (Plan 41-01)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request, Response

_errors: Any = import_module("backend.01_core.errors")
_resp: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.11_slo.schemas"
)
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.11_slo.service"
)
_repo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.11_slo.repository"
)

SloCreateRequest = _schemas.SloCreateRequest
SloUpdateRequest = _schemas.SloUpdateRequest
SloResponse = _schemas.SloResponse
SloEvaluationResponse = _schemas.SloEvaluationResponse

router = APIRouter(tags=["monitoring.slos"])


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
        session_id=getattr(state, "session_id", None)
            or request.headers.get("x-session-id"),
        org_id=org_id,
        workspace_id=getattr(state, "workspace_id", None)
            or request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", "") or _core_id.uuid7(),
        audit_category="user",
    )


# ── SLO CRUD ──────────────────────────────────────────────────────────────


@router.get("/v1/monitoring/slos", status_code=200)
async def list_slos_route(
    request: Request,
    status: str | None = Query(default=None),
    window_kind: str | None = Query(default=None),
    owner_user_id: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """List SLOs for the org with optional filters."""
    pool = request.app.state.pool
    org_id, _user = _scope(request)

    async with pool.acquire() as conn:
        slos, total = await _repo.list_slos(
            conn,
            org_id=org_id,
            status=status,
            window_kind=window_kind,
            owner_user_id=owner_user_id,
            q=q,
            limit=limit,
            offset=offset,
        )

    responses = [SloResponse.from_row(row).model_dump(mode="json") for row in slos]
    return _resp.success_list_response(
        responses, total=total, limit=limit, offset=offset
    )


@router.post("/v1/monitoring/slos", status_code=201)
async def create_slo_route(
    request: Request, body: SloCreateRequest,
) -> dict:
    """Create a new SLO with indicator and burn thresholds."""
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)

    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        slo_row = await _service.create_slo(
            conn, ctx,
            org_id=org_id,
            name=body.name,
            slug=body.slug,
            description=body.description,
            indicator_kind=body.indicator_kind,
            indicator=body.indicator.model_dump() if body.indicator else {},
            window_kind=body.window_kind,
            target_pct=body.target_pct,
            severity=body.severity,
            owner_user_id=body.owner_user_id,
            burn_thresholds=body.burn_thresholds.model_dump() if body.burn_thresholds else None,
        )

    return _resp.success(SloResponse.from_row(slo_row).model_dump(mode="json"))


@router.get("/v1/monitoring/slos/{id}", status_code=200)
async def get_slo_route(
    request: Request, id: str,
) -> dict:
    """Fetch a single SLO by ID."""
    pool = request.app.state.pool
    org_id, _user = _scope(request)

    async with pool.acquire() as conn:
        slo_row = await _repo.get_slo_by_id(conn, id)

    if not slo_row:
        raise _errors.AppError("NOT_FOUND", f"SLO {id!r} not found", 404)
    if slo_row["org_id"] != org_id:
        raise _errors.AppError("UNAUTHORIZED", "SLO not in your org", 403)

    return _resp.success(SloResponse.from_row(slo_row).model_dump(mode="json"))


@router.patch("/v1/monitoring/slos/{id}", status_code=200)
async def update_slo_route(
    request: Request, id: str, body: SloUpdateRequest,
) -> dict:
    """Partial update of an SLO."""
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)

    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        slo_row = await _service.update_slo(
            conn, ctx,
            slo_id=id,
            org_id=org_id,
            name=body.name,
            description=body.description,
            target_pct=body.target_pct,
            is_active=body.is_active,
            owner_user_id=body.owner_user_id,
            severity=body.severity,
            indicator=body.indicator.model_dump() if body.indicator else None,
            burn_thresholds=body.burn_thresholds.model_dump() if body.burn_thresholds else None,
        )

    return _resp.success(SloResponse.from_row(slo_row).model_dump(mode="json"))


@router.delete("/v1/monitoring/slos/{id}", status_code=204)
async def delete_slo_route(
    request: Request, id: str,
) -> Response:
    """Soft-delete an SLO."""
    pool = request.app.state.pool
    org_id, _user = _scope(request)
    ctx_base = _build_ctx(request)

    async with pool.acquire() as conn:
        ctx = replace(ctx_base, conn=conn)
        await _service.delete_slo(conn, ctx, slo_id=id, org_id=org_id)

    return Response(status_code=204)


# ── Evaluations time-series ───────────────────────────────────────────────


@router.get("/v1/monitoring/slos/{id}/evaluations", status_code=200)
async def list_evaluations_route(
    request: Request,
    id: str,
    from_ts: str | None = Query(default=None, description="ISO 8601 start time"),
    to_ts: str | None = Query(default=None, description="ISO 8601 end time"),
    granularity: str = Query(default="1h", description="1h, 1d, etc (advisory)"),
    limit: int = Query(default=100, ge=1, le=10000),
) -> dict:
    """Fetch evaluation time-series for an SLO."""
    pool = request.app.state.pool
    org_id, _user = _scope(request)

    async with pool.acquire() as conn:
        slo_row = await _repo.get_slo_by_id(conn, id)

    if not slo_row:
        raise _errors.AppError("NOT_FOUND", f"SLO {id!r} not found", 404)
    if slo_row["org_id"] != org_id:
        raise _errors.AppError("UNAUTHORIZED", "SLO not in your org", 403)

    # Default: past 30 days
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    from_dt = from_ts and datetime.fromisoformat(from_ts) or (now - timedelta(days=30))
    to_dt = to_ts and datetime.fromisoformat(to_ts) or now

    async with pool.acquire() as conn:
        evals = await _repo.list_evaluations(
            conn,
            slo_id=id,
            from_ts=from_dt,
            to_ts=to_dt,
            limit=limit,
        )

    responses = [
        SloEvaluationResponse.from_row(row).model_dump(mode="json")
        for row in evals
    ]
    return _resp.success_list_response(
        responses, total=len(responses), limit=limit, offset=0
    )


# ── Budget snapshot ───────────────────────────────────────────────────────


@router.get("/v1/monitoring/slos/{id}/budget", status_code=200)
async def get_budget_route(
    request: Request,
    id: str,
    at: str | None = Query(default=None, description="ISO 8601 timestamp; default now"),
) -> dict:
    """Point-in-time error budget snapshot for an SLO."""
    pool = request.app.state.pool
    org_id, _user = _scope(request)

    async with pool.acquire() as conn:
        slo_row = await _repo.get_slo_by_id(conn, id)

    if not slo_row:
        raise _errors.AppError("NOT_FOUND", f"SLO {id!r} not found", 404)
    if slo_row["org_id"] != org_id:
        raise _errors.AppError("UNAUTHORIZED", "SLO not in your org", 403)

    # Return latest evaluation as the budget snapshot.
    # In future, could support time-travel queries via 'at' param.
    latest_eval = {
        "attainment_pct": slo_row.get("attainment_pct", 0),
        "budget_remaining_pct": slo_row.get("budget_remaining_pct", 100),
        "status": slo_row.get("status", "healthy"),
        "evaluated_at": slo_row.get("created_at"),
    }
    return _resp.success(latest_eval)


__all__ = [
    "list_slos_route",
    "create_slo_route",
    "get_slo_route",
    "update_slo_route",
    "delete_slo_route",
    "list_evaluations_route",
    "get_budget_route",
]

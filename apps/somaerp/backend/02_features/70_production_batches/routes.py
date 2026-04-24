"""Production batches routes — /v1/somaerp/production/*."""

from __future__ import annotations

from datetime import date
from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.70_production_batches.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.70_production_batches.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")


router = APIRouter(
    prefix="/v1/somaerp/production",
    tags=["production", "batches"],
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


# ── Batches ────────────────────────────────────────────────────────────


@router.get("/batches")
async def list_batches(
    request: Request,
    kitchen_id: str | None = Query(default=None),
    product_id: str | None = Query(default=None),
    recipe_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    run_date_from: str | None = Query(default=None),
    run_date_to: str | None = Query(default=None),
    lead_user_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_batches(
            conn,
            tenant_id=workspace_id,
            kitchen_id=kitchen_id,
            product_id=product_id,
            recipe_id=recipe_id,
            status=status,
            run_date_from=_parse_date(run_date_from),
            run_date_to=_parse_date(run_date_to),
            lead_user_id=lead_user_id,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.BatchOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/batches", status_code=201)
async def create_batch(
    request: Request, payload: _schemas.BatchCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.create_batch(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(_schemas.BatchOut(**row).model_dump(mode="json"))


@router.get("/batches/{batch_id}")
async def get_batch(request: Request, batch_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        detail = await _service.get_batch_detail(
            conn, tenant_id=workspace_id, batch_id=batch_id,
        )
    batch_out = _schemas.BatchOut(**detail["batch"]).model_dump(mode="json")
    steps_out = [
        _schemas.BatchStepLogOut(**s).model_dump(mode="json")
        for s in detail["steps"]
    ]
    cons_out = [
        _schemas.BatchConsumptionLineOut(**c).model_dump(mode="json")
        for c in detail["consumption"]
    ]
    qc_out = [
        _schemas.BatchQcResultOut(**q).model_dump(mode="json")
        for q in detail["qc_results"]
    ]
    summary_out = (
        _schemas.BatchSummaryOut(**detail["summary"]).model_dump(mode="json")
        if detail.get("summary") is not None
        else None
    )
    return _response.ok(
        {
            "batch": batch_out,
            "steps": steps_out,
            "consumption": cons_out,
            "qc_results": qc_out,
            "summary": summary_out,
        }
    )


@router.patch("/batches/{batch_id}")
async def patch_batch(
    request: Request, batch_id: str, payload: _schemas.BatchStatePatch,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.patch_batch(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            batch_id=batch_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.BatchOut(**row).model_dump(mode="json"))


@router.delete(
    "/batches/{batch_id}", status_code=204, response_class=Response,
)
async def delete_batch(request: Request, batch_id: str) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_batch(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            batch_id=batch_id,
        )
    return Response(status_code=204)


# ── Summary ────────────────────────────────────────────────────────────


@router.get("/batches/{batch_id}/summary")
async def get_batch_summary(request: Request, batch_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_batch_summary(
            conn, tenant_id=workspace_id, batch_id=batch_id,
        )
    return _response.ok(
        _schemas.BatchSummaryOut(**row).model_dump(mode="json"),
    )


# ── Steps ──────────────────────────────────────────────────────────────


@router.get("/batches/{batch_id}/steps")
async def list_batch_steps(request: Request, batch_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_batch_steps(
            conn, tenant_id=workspace_id, batch_id=batch_id,
        )
    data = [
        _schemas.BatchStepLogOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


@router.patch("/batches/{batch_id}/steps/{step_id}")
async def patch_batch_step(
    request: Request,
    batch_id: str,
    step_id: str,
    payload: _schemas.BatchStepPatch,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.patch_batch_step(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            batch_id=batch_id,
            step_id=step_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(
        _schemas.BatchStepLogOut(**row).model_dump(mode="json"),
    )


# ── Consumption ────────────────────────────────────────────────────────


@router.get("/batches/{batch_id}/consumption")
async def list_batch_consumption(request: Request, batch_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_batch_consumption(
            conn, tenant_id=workspace_id, batch_id=batch_id,
        )
    data = [
        _schemas.BatchConsumptionLineOut(**r).model_dump(mode="json")
        for r in rows
    ]
    return _response.ok(data)


@router.patch("/batches/{batch_id}/consumption/{line_id}")
async def patch_batch_consumption(
    request: Request,
    batch_id: str,
    line_id: str,
    payload: _schemas.BatchConsumptionPatch,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.patch_batch_consumption(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            batch_id=batch_id,
            line_id=line_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(
        _schemas.BatchConsumptionLineOut(**row).model_dump(mode="json"),
    )


# ── QC ─────────────────────────────────────────────────────────────────


@router.get("/batches/{batch_id}/qc")
async def list_batch_qc(request: Request, batch_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_batch_qc_results(
            conn, tenant_id=workspace_id, batch_id=batch_id,
        )
    data = [
        _schemas.BatchQcResultOut(**r).model_dump(mode="json") for r in rows
    ]
    return _response.ok(data)


@router.post("/batches/{batch_id}/qc", status_code=201)
async def record_batch_qc(
    request: Request,
    batch_id: str,
    payload: _schemas.BatchQcResultCreate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.record_batch_qc(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            batch_id=batch_id,
            data=payload.model_dump(mode="python"),
        )
    return _response.ok(
        _schemas.BatchQcResultOut(**row).model_dump(mode="json"),
    )


# ── Today's board ──────────────────────────────────────────────────────


@router.get("/board")
async def todays_board(
    request: Request,
    on_date: str | None = Query(default=None, alias="date"),
) -> dict:
    workspace_id = _require_workspace(request)
    target_date = _parse_date(on_date) or date.today()
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        groups = await _service.get_todays_board(
            conn, tenant_id=workspace_id, on_date=target_date,
        )
    out: list[dict] = []
    for g in groups:
        batches_out = []
        for item in g["batches"]:
            b_out = _schemas.BatchOut(**item["batch"]).model_dump(mode="json")
            s_out = (
                _schemas.BatchSummaryOut(**item["summary"]).model_dump(mode="json")
                if item.get("summary") is not None
                else None
            )
            batches_out.append({"batch": b_out, "summary": s_out})
        out.append(
            {
                "kitchen_id": g["kitchen_id"],
                "kitchen_name": g["kitchen_name"],
                "batches": batches_out,
            }
        )
    return _response.ok({"date": target_date.isoformat(), "kitchens": out})

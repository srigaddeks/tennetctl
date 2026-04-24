"""Quality routes — /v1/somaerp/quality/*.

Endpoints:
  - GET /check-types (read-only)
  - GET /stages       (read-only)
  - GET /outcomes     (read-only)
  - GET/POST /checkpoints + GET/PATCH/DELETE /checkpoints/{id}
  - GET/POST /checks + GET /checks/{id}   (append-only — no PATCH/DELETE)
"""

from __future__ import annotations

from datetime import datetime
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Body, Query, Request, Response

_service = import_module(
    "apps.somaerp.backend.02_features.50_quality.service",
)
_schemas = import_module(
    "apps.somaerp.backend.02_features.50_quality.schemas",
)
_response = import_module("apps.somaerp.backend.01_core.response")
_errors = import_module("apps.somaerp.backend.01_core.errors")


router = APIRouter(
    prefix="/v1/somaerp/quality",
    tags=["quality"],
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


# ── Lookups (read-only) ────────────────────────────────────────────────


@router.get("/check-types")
async def list_check_types(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_check_types(conn)
    data = [_schemas.QcCheckTypeOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.get("/stages")
async def list_stages(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_stages(conn)
    data = [_schemas.QcStageOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.get("/outcomes")
async def list_outcomes(request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_outcomes(conn)
    data = [_schemas.QcOutcomeOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


# ── Checkpoints CRUD ───────────────────────────────────────────────────


@router.get("/checkpoints")
async def list_checkpoints(
    request: Request,
    scope_kind: str | None = Query(default=None),
    scope_ref_id: str | None = Query(default=None),
    stage_id: int | None = Query(default=None),
    check_type_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_checkpoints(
            conn,
            tenant_id=workspace_id,
            scope_kind=scope_kind,
            scope_ref_id=scope_ref_id,
            stage_id=stage_id,
            check_type_id=check_type_id,
            status=status,
            q=q,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
        )
    data = [_schemas.QcCheckpointOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/checkpoints", status_code=201)
async def create_checkpoint(
    request: Request, payload: Any = Body(...),
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    if isinstance(payload, list):
        items = [_schemas.QcCheckpointCreate(**p) for p in payload]
    else:
        items = [_schemas.QcCheckpointCreate(**payload)]

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    created: list[dict] = []
    async with pool.acquire() as conn:
        for item in items:
            row = await _service.create_checkpoint(
                conn,
                tennetctl=tennetctl,
                tenant_id=workspace_id,
                actor_user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                data=item.model_dump(mode="python"),
            )
            created.append(
                _schemas.QcCheckpointOut(**row).model_dump(mode="json"),
            )
    return _response.ok(created if isinstance(payload, list) else created[0])


@router.get("/checkpoints/{checkpoint_id}")
async def get_checkpoint(request: Request, checkpoint_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_checkpoint(
            conn, tenant_id=workspace_id, checkpoint_id=checkpoint_id,
        )
    return _response.ok(_schemas.QcCheckpointOut(**row).model_dump(mode="json"))


@router.patch("/checkpoints/{checkpoint_id}")
async def patch_checkpoint(
    request: Request,
    checkpoint_id: str,
    payload: _schemas.QcCheckpointUpdate,
) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        row = await _service.update_checkpoint(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            checkpoint_id=checkpoint_id,
            patch=payload.model_dump(exclude_unset=True, mode="python"),
        )
    return _response.ok(_schemas.QcCheckpointOut(**row).model_dump(mode="json"))


@router.delete(
    "/checkpoints/{checkpoint_id}", status_code=204, response_class=Response,
)
async def delete_checkpoint(
    request: Request, checkpoint_id: str,
) -> Response:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        await _service.soft_delete_checkpoint(
            conn,
            tennetctl=tennetctl,
            tenant_id=workspace_id,
            actor_user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            checkpoint_id=checkpoint_id,
        )
    return Response(status_code=204)


# ── Checks (append-only) ───────────────────────────────────────────────


@router.get("/checks")
async def list_checks(
    request: Request,
    checkpoint_id: str | None = Query(default=None),
    batch_id: str | None = Query(default=None),
    outcome_id: int | None = Query(default=None),
    kitchen_id: str | None = Query(default=None),
    raw_material_lot: str | None = Query(default=None),
    performed_by_user_id: str | None = Query(default=None),
    ts_after: str | None = Query(default=None),
    ts_before: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_checks(
            conn,
            tenant_id=workspace_id,
            checkpoint_id=checkpoint_id,
            batch_id=batch_id,
            outcome_id=outcome_id,
            kitchen_id=kitchen_id,
            raw_material_lot=raw_material_lot,
            performed_by_user_id=performed_by_user_id,
            ts_after=_parse_ts(ts_after),
            ts_before=_parse_ts(ts_before),
            limit=limit,
            offset=offset,
        )
    data = [_schemas.QcCheckOut(**r).model_dump(mode="json") for r in rows]
    return _response.ok(data)


@router.post("/checks", status_code=201)
async def create_check(request: Request, payload: Any = Body(...)) -> dict:
    workspace_id = _require_workspace(request)
    user_id = getattr(request.state, "user_id", None)
    org_id = getattr(request.state, "org_id", None)
    session_id = getattr(request.state, "session_id", None)

    if isinstance(payload, list):
        items = [_schemas.QcCheckCreate(**p) for p in payload]
    else:
        items = [_schemas.QcCheckCreate(**payload)]

    pool = request.app.state.pool
    tennetctl = request.app.state.tennetctl
    created: list[dict] = []
    async with pool.acquire() as conn:
        for item in items:
            row = await _service.create_check(
                conn,
                tennetctl=tennetctl,
                tenant_id=workspace_id,
                actor_user_id=user_id,
                org_id=org_id,
                session_id=session_id,
                data=item.model_dump(mode="python"),
            )
            created.append(_schemas.QcCheckOut(**row).model_dump(mode="json"))
    return _response.ok(created if isinstance(payload, list) else created[0])


@router.get("/checks/{check_id}")
async def get_check(request: Request, check_id: str) -> dict:
    workspace_id = _require_workspace(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_check(
            conn, tenant_id=workspace_id, check_id=check_id,
        )
    return _response.ok(_schemas.QcCheckOut(**row).model_dump(mode="json"))

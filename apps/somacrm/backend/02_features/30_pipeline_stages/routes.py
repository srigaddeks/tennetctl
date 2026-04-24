"""Pipeline stage routes — /v1/somacrm/pipeline-stages."""

from __future__ import annotations

from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module("apps.somacrm.backend.02_features.30_pipeline_stages.service")
_schemas = import_module("apps.somacrm.backend.02_features.30_pipeline_stages.schemas")
_response = import_module("apps.somacrm.backend.01_core.response")
_errors = import_module("apps.somacrm.backend.01_core.errors")

router = APIRouter(prefix="/v1/somacrm/pipeline-stages", tags=["pipeline-stages"])


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("")
async def list_pipeline_stages(
    request: Request,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        rows = await _service.list_pipeline_stages(conn, tenant_id=workspace_id, limit=limit, offset=offset)
    return _response.ok([_schemas.PipelineStageOut(**r).model_dump(mode="json") for r in rows])


@router.post("", status_code=201)
async def create_pipeline_stage(request: Request, payload: _schemas.PipelineStageCreate) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.create_pipeline_stage(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            data=payload.model_dump(),
        )
    return _response.ok(_schemas.PipelineStageOut(**row).model_dump(mode="json"))


@router.get("/{stage_id}")
async def get_pipeline_stage(request: Request, stage_id: str) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.get_pipeline_stage(conn, tenant_id=workspace_id, stage_id=stage_id)
    return _response.ok(_schemas.PipelineStageOut(**row).model_dump(mode="json"))


@router.patch("/{stage_id}")
async def patch_pipeline_stage(request: Request, stage_id: str, payload: _schemas.PipelineStageUpdate) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.update_pipeline_stage(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            stage_id=stage_id,
            patch=payload.model_dump(exclude_unset=True),
        )
    return _response.ok(_schemas.PipelineStageOut(**row).model_dump(mode="json"))


@router.delete("/{stage_id}", status_code=204, response_class=Response)
async def delete_pipeline_stage(request: Request, stage_id: str) -> Response:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        await _service.soft_delete_pipeline_stage(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            stage_id=stage_id,
        )
    return Response(status_code=204)

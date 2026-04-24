"""Tag routes — /v1/somacrm/tags and /v1/somacrm/entity-tags."""

from __future__ import annotations

from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module("apps.somacrm.backend.02_features.50_tags.service")
_schemas = import_module("apps.somacrm.backend.02_features.50_tags.schemas")
_response = import_module("apps.somacrm.backend.01_core.response")
_errors = import_module("apps.somacrm.backend.01_core.errors")

router = APIRouter(prefix="/v1/somacrm/tags", tags=["tags"])
entity_tags_router = APIRouter(prefix="/v1/somacrm/entity-tags", tags=["tags"])


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("")
async def list_tags(
    request: Request,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        rows = await _service.list_tags(conn, tenant_id=workspace_id, limit=limit, offset=offset)
    return _response.ok([_schemas.TagOut(**r).model_dump(mode="json") for r in rows])


@router.post("", status_code=201)
async def create_tag(request: Request, payload: _schemas.TagCreate) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.create_tag(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            data=payload.model_dump(),
        )
    return _response.ok(_schemas.TagOut(**row).model_dump(mode="json"))


@router.delete("/{tag_id}", status_code=204, response_class=Response)
async def delete_tag(request: Request, tag_id: str) -> Response:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        await _service.soft_delete_tag(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            tag_id=tag_id,
        )
    return Response(status_code=204)


@entity_tags_router.post("", status_code=201)
async def create_entity_tag(request: Request, payload: _schemas.EntityTagCreate) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.create_entity_tag(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            data=payload.model_dump(),
        )
    return _response.ok(_schemas.EntityTagOut(**row).model_dump(mode="json"))


@entity_tags_router.delete("/{entity_tag_id}", status_code=204, response_class=Response)
async def delete_entity_tag(request: Request, entity_tag_id: str) -> Response:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        await _service.delete_entity_tag(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            entity_tag_id=entity_tag_id,
        )
    return Response(status_code=204)

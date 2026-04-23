"""Idea routes — /v1/ideas."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request, Response

_service = import_module("apps.solsocial.backend.02_features.50_ideas.service")
_schemas = import_module("apps.solsocial.backend.02_features.50_ideas.schemas")
_authz = import_module("apps.solsocial.backend.01_core.authz")
_response = import_module("apps.solsocial.backend.01_core.response")

router = APIRouter(tags=["ideas"])


@router.get("/v1/ideas")
async def list_ideas(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "ideas.read")
        items = await _service.list_ideas(
            conn, workspace_id=identity["workspace_id"], limit=limit, offset=offset,
        )
    validated = [_schemas.IdeaOut(**r).model_dump() for r in items]
    return _response.success_list_response(validated, limit=limit, offset=offset)


@router.get("/v1/ideas/{idea_id}")
async def get_idea(request: Request, idea_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "ideas.read")
        row = await _service.get_idea(
            conn, idea_id=idea_id, workspace_id=identity["workspace_id"],
        )
    return _response.success(_schemas.IdeaOut(**row).model_dump())


@router.post("/v1/ideas", status_code=201)
async def create_idea(request: Request, payload: _schemas.IdeaIn) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "ideas.manage")
        row = await _service.create_idea(
            conn,
            org_id=identity["org_id"],
            workspace_id=identity["workspace_id"],
            created_by=identity["user_id"],
            title=payload.title, notes=payload.notes, tags=payload.tags,
        )
    return _response.success(_schemas.IdeaOut(**row).model_dump())


@router.patch("/v1/ideas/{idea_id}")
async def patch_idea(request: Request, idea_id: str, payload: _schemas.IdeaPatch) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "ideas.manage")
        row = await _service.patch_idea(
            conn, idea_id=idea_id, workspace_id=identity["workspace_id"],
            title=payload.title, notes=payload.notes, tags=payload.tags,
        )
    return _response.success(_schemas.IdeaOut(**row).model_dump())


@router.delete("/v1/ideas/{idea_id}", response_class=Response, status_code=204)
async def delete_idea(request: Request, idea_id: str) -> Response:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "ideas.manage")
        await _service.delete_idea(
            conn, idea_id=idea_id, workspace_id=identity["workspace_id"],
        )
    return Response(status_code=204)

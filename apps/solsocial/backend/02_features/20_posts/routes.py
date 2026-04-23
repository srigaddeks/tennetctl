"""Post routes — /v1/posts."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Query, Request, Response

_service = import_module("apps.solsocial.backend.02_features.20_posts.service")
_schemas = import_module("apps.solsocial.backend.02_features.20_posts.schemas")
_authz = import_module("apps.solsocial.backend.01_core.authz")
_response = import_module("apps.solsocial.backend.01_core.response")

router = APIRouter(tags=["posts"])


@router.get("/v1/posts")
async def list_posts(
    request: Request,
    status: str | None = Query(default=None),
    channel_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "posts.read")
        items = await _service.list_posts(
            conn, workspace_id=identity["workspace_id"], status=status,
            channel_id=channel_id, limit=limit, offset=offset,
        )
    validated = [_schemas.PostOut(**r).model_dump() for r in items]
    return _response.success_list_response(validated, limit=limit, offset=offset)


@router.get("/v1/posts/{post_id}")
async def get_post(request: Request, post_id: str) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "posts.read")
        row = await _service.get_post(
            conn, post_id=post_id, workspace_id=identity["workspace_id"],
        )
    return _response.success(_schemas.PostOut(**row).model_dump())


@router.post("/v1/posts", status_code=201)
async def create_post(request: Request, payload: _schemas.PostCreate) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "posts.create")
        row = await _service.create_post(
            conn,
            org_id=identity["org_id"],
            workspace_id=identity["workspace_id"],
            channel_id=payload.channel_id,
            body=payload.body,
            media=[m.model_dump() for m in payload.media],
            link=payload.link,
            status=payload.status,
            scheduled_at=payload.scheduled_at,
            created_by=identity["user_id"],
        )
    client = request.app.state.tennetctl
    await client.emit_audit(
        event_key="solsocial.posts.created", outcome="success",
        metadata={"post_id": row["id"], "channel_id": row["channel_id"]},
        actor_user_id=identity["user_id"],
        org_id=identity["org_id"],
        workspace_id=identity["workspace_id"],
    )
    return _response.success(_schemas.PostOut(**row).model_dump())


@router.patch("/v1/posts/{post_id}")
async def patch_post(request: Request, post_id: str, payload: _schemas.PostPatch) -> Any:
    pool = request.app.state.pool
    fields_set = payload.model_fields_set
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "posts.update")
        row = await _service.patch_post(
            conn,
            post_id=post_id,
            workspace_id=identity["workspace_id"],
            body=payload.body,
            media=[m.model_dump() for m in payload.media] if payload.media is not None else None,
            link=payload.link,
            status=payload.status,
            scheduled_at=payload.scheduled_at,
            scheduled_at_set="scheduled_at" in fields_set,
        )
    return _response.success(_schemas.PostOut(**row).model_dump())


@router.delete("/v1/posts/{post_id}", response_class=Response, status_code=204)
async def delete_post(request: Request, post_id: str) -> Response:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "posts.delete")
        await _service.delete_post(
            conn, post_id=post_id, workspace_id=identity["workspace_id"],
        )
    return Response(status_code=204)


@router.post("/v1/posts/{post_id}/publish")
async def publish_post(request: Request, post_id: str) -> Any:
    """Publish a post immediately. Runs the provider publisher pipeline."""
    pool = request.app.state.pool
    publisher = request.app.state.publisher
    tennetctl = request.app.state.tennetctl
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "posts.publish")
        row = await _service.publish_now(
            conn, post_id=post_id, workspace_id=identity["workspace_id"],
            publisher=publisher, tennetctl=tennetctl, token=identity["token"],
        )
    await tennetctl.emit_audit(
        event_key="solsocial.posts.published", outcome="success",
        metadata={"post_id": row["id"]},
        actor_user_id=identity["user_id"],
        org_id=identity["org_id"],
        workspace_id=identity["workspace_id"],
    )
    return _response.success(_schemas.PostOut(**row).model_dump())

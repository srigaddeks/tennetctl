"""
social_publisher — FastAPI routes.

Endpoints:
  POST   /v1/social/accounts            — connect account
  GET    /v1/social/accounts            — list accounts
  DELETE /v1/social/accounts/{id}       — disconnect account
  GET    /v1/social/posts               — list posts
  POST   /v1/social/posts               — create post
  GET    /v1/social/posts/{id}          — get post
  PATCH  /v1/social/posts/{id}          — update post
  DELETE /v1/social/posts/{id}          — soft delete post (204)
  POST   /v1/social/posts/{id}/publish  — publish now
  GET    /v1/social/posts/{id}/metrics  — get metrics
  POST   /v1/social/posts/{id}/metrics/refresh — pull fresh metrics
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request, Response

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module("backend.02_features.07_social_publisher.schemas")
_service: Any = import_module("backend.02_features.07_social_publisher.service")

SocialAccountCreate = _schemas.SocialAccountCreate
PostCreate = _schemas.PostCreate
PostUpdate = _schemas.PostUpdate

router = APIRouter(prefix="/v1/social", tags=["social_publisher"])


def _build_ctx(request: Request, pool: Any) -> Any:
    vault = getattr(request.app.state, "vault", None)
    return _catalog_ctx.NodeContext(
        user_id=request.headers.get("x-user-id"),
        session_id=request.headers.get("x-session-id"),
        org_id=request.headers.get("x-org-id"),
        workspace_id=request.headers.get("x-workspace-id"),
        application_id=getattr(request.state, "application_id", None) or request.headers.get("x-application-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="system",
        pool=pool,
        extras={"pool": pool, "vault": vault},
    )


def _get_vault(request: Request) -> Any:
    vault = getattr(request.app.state, "vault", None)
    if vault is None:
        raise _errors.AppError(
            "VAULT_UNAVAILABLE",
            "Vault is not enabled. Enable the 'vault' module.",
            503,
        )
    return vault


def _org_id_from(request: Request, query_org_id: str | None = None) -> str:
    org_id = query_org_id or request.headers.get("x-org-id")
    if not org_id:
        raise _errors.AppError("MISSING_ORG", "org_id is required (header x-org-id or query param).", 400)
    return org_id


# ── Accounts ─────────────────────────────────────────────────────────────────

@router.post("/accounts", status_code=201)
async def connect_account_route(request: Request, body: SocialAccountCreate) -> dict:
    vault = _get_vault(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    # Allow org_id from body if not in header (for setup flows)
    if not getattr(ctx, "org_id", None):
        raise _errors.AppError("MISSING_ORG", "x-org-id header is required.", 400)
    row = await _service.connect_account(pool, vault, ctx, body.model_dump())
    return _response.success(row)


@router.get("/accounts", status_code=200)
async def list_accounts_route(
    request: Request,
    org_id: str | None = None,
) -> dict:
    pool = request.app.state.pool
    _ctx = _build_ctx(request, pool)  # available for audit if needed
    resolved_org_id = _org_id_from(request, org_id)
    items = await _service.list_accounts(pool, resolved_org_id)
    return _response.success({"items": items, "total": len(items)})


@router.delete("/accounts/{account_id}", status_code=204)
async def disconnect_account_route(request: Request, account_id: str) -> Response:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    await _service.disconnect_account(pool, ctx, account_id)
    return Response(status_code=204)


# ── Posts ─────────────────────────────────────────────────────────────────────

@router.get("/posts", status_code=200)
async def list_posts_route(
    request: Request,
    org_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    pool = request.app.state.pool
    _ctx = _build_ctx(request, pool)  # available for audit if needed
    resolved_org_id = _org_id_from(request, org_id)
    items, total = await _service.list_posts(pool, resolved_org_id, status=status, limit=limit, offset=offset)
    return _response.paginated(items, total=total, limit=limit, offset=offset)


@router.post("/posts", status_code=201)
async def create_post_route(request: Request, body: PostCreate) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    post = await _service.create_post(pool, ctx, body.model_dump())
    return _response.success(post)


@router.get("/posts/{post_id}", status_code=200)
async def get_post_route(request: Request, post_id: str) -> dict:
    pool = request.app.state.pool
    post = await _service.get_post(pool, post_id)
    if post is None:
        raise _errors.NotFoundError(f"Post {post_id!r} not found.")
    return _response.success(post)


@router.patch("/posts/{post_id}", status_code=200)
async def update_post_route(request: Request, post_id: str, body: PostUpdate) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    post = await _service.update_post(pool, ctx, post_id, body.model_dump(exclude_none=True))
    return _response.success(post)


@router.delete("/posts/{post_id}", status_code=204)
async def delete_post_route(request: Request, post_id: str) -> Response:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    await _service.delete_post(pool, ctx, post_id)
    return Response(status_code=204)


@router.post("/posts/{post_id}/publish", status_code=200)
async def publish_now_route(request: Request, post_id: str) -> dict:
    vault = _get_vault(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    post = await _service.publish_post_now(pool, vault, ctx, post_id)
    return _response.success(post)


@router.get("/posts/{post_id}/metrics", status_code=200)
async def get_metrics_route(request: Request, post_id: str) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items = await _service.get_post_metrics(conn, post_id=post_id)
    return _response.success({"items": items, "total": len(items)})


@router.post("/posts/{post_id}/metrics/refresh", status_code=200)
async def refresh_metrics_route(request: Request, post_id: str) -> dict:
    vault = _get_vault(request)
    pool = request.app.state.pool
    items = await _service.refresh_metrics(pool, vault, post_id)
    return _response.success({"items": items, "total": len(items)})

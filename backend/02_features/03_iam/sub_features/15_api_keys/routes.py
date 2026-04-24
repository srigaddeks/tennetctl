"""Routes for iam.api_keys at /v1/api-keys.

Session-authenticated only (users manage their own keys via the UI). API keys
cannot be used to mint more API keys — that would turn a leaked key into a
key-generation oracle.
"""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_errors: Any = import_module("backend.01_core.errors")
_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_schemas: Any = import_module("backend.02_features.03_iam.sub_features.15_api_keys.schemas")
_service: Any = import_module("backend.02_features.03_iam.sub_features.15_api_keys.service")
_authz: Any = import_module("backend.02_features.03_iam.sub_features.29_authz_gates.authz_helpers")

ApiKeyCreate = _schemas.ApiKeyCreate
ApiKeyRow = _schemas.ApiKeyRow
ApiKeyCreatedResponse = _schemas.ApiKeyCreatedResponse


router = APIRouter(prefix="/v1/api-keys", tags=["iam.api_keys"])


def _build_ctx(request: Request, pool: Any) -> Any:
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None),
        session_id=getattr(state, "session_id", None),
        org_id=getattr(state, "org_id", None),
        workspace_id=getattr(state, "workspace_id", None),
        application_id=getattr(request.state, "application_id", None) or request.headers.get("x-application-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(state, "request_id", None) or _core_id.uuid7(),
        audit_category="setup",
        pool=pool,
        extras={"pool": pool},
    )


def _require_session(request: Request) -> tuple[str, str | None]:
    """Return (user_id, org_id) from the session — API keys can't mint keys.

    `org_id` may be None if the user has no active org association. The key
    record still captures whichever org is on the session.
    """
    user_id = getattr(request.state, "user_id", None)
    session_id = getattr(request.state, "session_id", None)
    if not user_id or not session_id:
        raise _errors.AppError(
            "UNAUTHORIZED", "Session authentication required to manage API keys.", 401
        )
    org_id = getattr(request.state, "org_id", None)
    return user_id, org_id


@router.get("", status_code=200)
async def list_api_keys_route(request: Request) -> dict:
    user_id, org_id = _require_session(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items = await _service.list_api_keys(conn, org_id=org_id, user_id=user_id)
    data = [ApiKeyRow(**r).model_dump() for r in items]
    return _response.success({"items": data, "total": len(data)})


@router.post("", status_code=201)
async def create_api_key_route(request: Request, body: ApiKeyCreate) -> dict:
    user_id, org_id = _require_session(request)
    pool = request.app.state.pool
    vault = request.app.state.vault
    ctx = _build_ctx(request, pool)
    # For users without an active org, store the key against the user's uuid
    # as the org placeholder — keeps the NOT NULL constraint honest and the
    # user still owns their own key exclusively.
    effective_org = org_id or user_id
    async with pool.acquire() as conn:
        ctx2 = replace(ctx, conn=conn)
        row = await _service.mint_api_key(
            conn, pool, ctx2, vault,
            org_id=effective_org,
            user_id=user_id,
            label=body.label,
            scopes=body.scopes,
            expires_at=body.expires_at,
        )
    return _response.success(ApiKeyCreatedResponse(**row).model_dump())


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key_route(request: Request, key_id: str) -> None:
    user_id, org_id = _require_session(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        # Cross-org ownership check: the key must belong to the authenticated
        # user in the session org. Prevents one user revoking another org's keys.
        key_row = await _service._repo.get_by_id(conn, key_id=key_id)
        if key_row is None:
            raise _errors.NotFoundError(f"api key {key_id!r} not found or already revoked")
        if key_row.get("user_id") != user_id or key_row.get("org_id") != (org_id or user_id):
            raise _errors.ForbiddenError("Access denied: key does not belong to your account.")
        ctx2 = replace(ctx, conn=conn)
        deleted = await _service.revoke_api_key(conn, pool, ctx2, key_id=key_id)
    if not deleted:
        raise _errors.NotFoundError(f"api key {key_id!r} not found or already revoked")


@router.post("/{key_id}/rotate", status_code=200)
async def rotate_api_key_route(request: Request, key_id: str) -> dict:
    user_id, org_id = _require_session(request)
    pool = request.app.state.pool
    vault = request.app.state.vault
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        # Cross-org ownership check: the key must belong to the authenticated
        # user in the session org. Prevents one user rotating another org's keys.
        key_row = await _service._repo.get_by_id(conn, key_id=key_id)
        if key_row is None:
            raise _errors.AppError("NOT_FOUND", f"api key {key_id!r} not found or already revoked.", 404)
        if key_row.get("user_id") != user_id or key_row.get("org_id") != (org_id or user_id):
            raise _errors.ForbiddenError("Access denied: key does not belong to your account.")
        ctx2 = replace(ctx, conn=conn)
        row = await _service.rotate_api_key(conn, pool, ctx2, vault, key_id=key_id)
    return _response.success(ApiKeyCreatedResponse(**row).model_dump())

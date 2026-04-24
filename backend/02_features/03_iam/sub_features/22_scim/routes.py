"""iam.scim — FastAPI routes: admin token CRUD + SCIM 2.0 Users/Groups endpoints."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

_resp: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.22_scim.service"
)
_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.22_scim.schemas"
)
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")

ScimTokenCreate = _schemas.ScimTokenCreate
ScimTokenRow = _schemas.ScimTokenRow

# ── Admin token routes ────────────────────────────────────────────────────────

router = APIRouter(prefix="/v1/iam/scim-tokens", tags=["iam.scim.admin"])


def _require_org_id(request: Request) -> str:
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise _errors.UnauthorizedError("org context required")
    return org_id


def _build_ctx(request: Request, pool: Any) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=getattr(request.state, "user_id", None),
        session_id=getattr(request.state, "session_id", None),
        org_id=getattr(request.state, "org_id", None),
        workspace_id=getattr(request.state, "workspace_id", None),
        application_id=getattr(request.state, "application_id", None) or request.headers.get("x-application-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="admin",
        pool=pool,
        extras={"pool": pool},
    )


@router.get("")
async def list_tokens(request: Request) -> Any:
    org_id = _require_org_id(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_scim_tokens(conn, org_id)
    return _resp.success_response([ScimTokenRow(**r).model_dump(mode="json") for r in rows])


@router.post("", status_code=201)
async def create_token(request: Request, body: ScimTokenCreate) -> Any:
    org_id = _require_org_id(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        row, raw_token = await _service.create_scim_token(pool, conn, ctx, org_id=org_id, label=body.label)
    data = {**ScimTokenRow(**row).model_dump(mode="json"), "token": raw_token}
    return JSONResponse(content=_resp.success(data), status_code=201)


@router.delete("/{token_id}", status_code=204)
async def revoke_token(token_id: str, request: Request) -> None:
    org_id = _require_org_id(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        await _service.revoke_scim_token(pool, conn, ctx, token_id=token_id, org_id=org_id)
    return None


# ── SCIM 2.0 endpoints ────────────────────────────────────────────────────────

scim_router = APIRouter(prefix="/scim/v2", tags=["iam.scim.v2"])

SCIM_CONTENT_TYPE = "application/scim+json"


def _scim_response(data: dict, status: int = 200) -> JSONResponse:
    return JSONResponse(content=data, status_code=status, media_type=SCIM_CONTENT_TYPE)


def _scim_error(status: int, detail: str) -> JSONResponse:
    return _scim_response(_schemas.scim_error(status, detail), status)


async def _scim_auth(request: Request, org_slug: str) -> dict:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise ValueError("Missing bearer token")
    bearer = auth[7:].strip()
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        org = await _service.authenticate_scim_request(conn, org_slug=org_slug, bearer=bearer)
    return org


def _scim_ctx(request: Request, pool: Any, org: dict) -> Any:
    return _catalog_ctx.NodeContext(
        user_id="scim", session_id=None,
        org_id=org["id"], workspace_id=None,
        trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(),
        audit_category="setup",
        pool=pool,
        extras={"pool": pool},
    )


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


# ── Users ─────────────────────────────────────────────────────────────────────

@scim_router.get("/{org_slug}/Users")
async def scim_list_users(org_slug: str, request: Request) -> Any:
    try:
        org = await _scim_auth(request, org_slug)
    except Exception:
        return _scim_error(401, "Unauthorized")
    filter_str = request.query_params.get("filter")
    start_index = int(request.query_params.get("startIndex", 1))
    count = int(request.query_params.get("count", 100))
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        users, total = await _service.list_users(
            conn, org_id=org["id"], filter_str=filter_str, start_index=start_index, count=count,
        )
    resources = [_schemas.scim_user(u, _base_url(request), org_slug) for u in users]
    return _scim_response(_schemas.scim_list(resources, total, start_index))


@scim_router.post("/{org_slug}/Users", status_code=201)
async def scim_create_user(org_slug: str, request: Request) -> Any:
    try:
        org = await _scim_auth(request, org_slug)
    except Exception:
        return _scim_error(401, "Unauthorized")
    body = await request.json()
    pool = request.app.state.pool
    ctx = _scim_ctx(request, pool, org)
    user_name = body.get("userName", "")
    display_name = (body.get("name") or {}).get("formatted") or body.get("displayName") or user_name
    active = body.get("active", True)
    external_id = body.get("externalId")
    try:
        async with pool.acquire() as conn:
            user = await _service.create_user(
                pool, conn, ctx,
                user_name=user_name, display_name=display_name,
                active=active, external_id=external_id,
            )
    except _errors.AppError as exc:
        return _scim_error(exc.status_code, exc.message)
    return _scim_response(_schemas.scim_user(user, _base_url(request), org_slug), 201)


@scim_router.get("/{org_slug}/Users/{user_id}")
async def scim_get_user(org_slug: str, user_id: str, request: Request) -> Any:
    try:
        await _scim_auth(request, org_slug)
    except Exception:
        return _scim_error(401, "Unauthorized")
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            user = await _service.get_user(conn, user_id)
    except _errors.NotFoundError as exc:
        return _scim_error(404, str(exc))
    return _scim_response(_schemas.scim_user(user, _base_url(request), org_slug))


@scim_router.patch("/{org_slug}/Users/{user_id}")
async def scim_patch_user(org_slug: str, user_id: str, request: Request) -> Any:
    try:
        org = await _scim_auth(request, org_slug)
    except Exception:
        return _scim_error(401, "Unauthorized")
    body = await request.json()
    ops = body.get("Operations", [])
    pool = request.app.state.pool
    ctx = _scim_ctx(request, pool, org)
    try:
        async with pool.acquire() as conn:
            user = await _service.update_user(pool, conn, ctx, user_id=user_id, patch_ops=ops)
    except _errors.NotFoundError as exc:
        return _scim_error(404, str(exc))
    return _scim_response(_schemas.scim_user(user, _base_url(request), org_slug))


@scim_router.delete("/{org_slug}/Users/{user_id}", status_code=204)
async def scim_delete_user(org_slug: str, user_id: str, request: Request) -> None:
    try:
        org = await _scim_auth(request, org_slug)
    except Exception:
        return _scim_error(401, "Unauthorized")
    pool = request.app.state.pool
    ctx = _scim_ctx(request, pool, org)
    try:
        async with pool.acquire() as conn:
            await _service.deprovision_user(pool, conn, ctx, user_id=user_id)
    except _errors.NotFoundError as exc:
        return _scim_error(404, str(exc))
    return None


# ── Groups ────────────────────────────────────────────────────────────────────

@scim_router.get("/{org_slug}/Groups")
async def scim_list_groups(org_slug: str, request: Request) -> Any:
    try:
        org = await _scim_auth(request, org_slug)
    except Exception:
        return _scim_error(401, "Unauthorized")
    filter_str = request.query_params.get("filter")
    start_index = int(request.query_params.get("startIndex", 1))
    count = int(request.query_params.get("count", 100))
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        groups, total = await _service.list_groups(
            conn, org_id=org["id"], filter_str=filter_str, start_index=start_index, count=count,
        )
    resources = [_schemas.scim_group(g, _base_url(request), org_slug) for g in groups]
    return _scim_response(_schemas.scim_list(resources, total, start_index))


@scim_router.post("/{org_slug}/Groups", status_code=201)
async def scim_create_group(org_slug: str, request: Request) -> Any:
    try:
        org = await _scim_auth(request, org_slug)
    except Exception:
        return _scim_error(401, "Unauthorized")
    body = await request.json()
    display_name = body.get("displayName", "")
    members = [m.get("value") for m in body.get("members", []) if m.get("value")]
    pool = request.app.state.pool
    ctx = _scim_ctx(request, pool, org)
    try:
        async with pool.acquire() as conn:
            group = await _service.create_group(pool, conn, ctx, org_id=org["id"],
                                                display_name=display_name, members=members)
    except _errors.AppError as exc:
        return _scim_error(exc.status_code, exc.message)
    m = group.pop("_members", [])
    return _scim_response(_schemas.scim_group(group, _base_url(request), org_slug, members=m), 201)


@scim_router.get("/{org_slug}/Groups/{group_id}")
async def scim_get_group(org_slug: str, group_id: str, request: Request) -> Any:
    try:
        await _scim_auth(request, org_slug)
    except Exception:
        return _scim_error(401, "Unauthorized")
    pool = request.app.state.pool
    try:
        async with pool.acquire() as conn:
            group = await _service.get_group(conn, group_id)
    except _errors.NotFoundError as exc:
        return _scim_error(404, str(exc))
    members = group.pop("_members", [])
    return _scim_response(_schemas.scim_group(group, _base_url(request), org_slug, members=members))


@scim_router.patch("/{org_slug}/Groups/{group_id}")
async def scim_patch_group(org_slug: str, group_id: str, request: Request) -> Any:
    try:
        org = await _scim_auth(request, org_slug)
    except Exception:
        return _scim_error(401, "Unauthorized")
    body = await request.json()
    ops = body.get("Operations", [])
    pool = request.app.state.pool
    ctx = _scim_ctx(request, pool, org)
    try:
        async with pool.acquire() as conn:
            group = await _service.patch_group(pool, conn, ctx, group_id=group_id, org_id=org["id"], patch_ops=ops)
    except _errors.NotFoundError as exc:
        return _scim_error(404, str(exc))
    members = group.pop("_members", [])
    return _scim_response(_schemas.scim_group(group, _base_url(request), org_slug, members=members))


@scim_router.delete("/{org_slug}/Groups/{group_id}", status_code=204)
async def scim_delete_group(org_slug: str, group_id: str, request: Request) -> None:
    try:
        org = await _scim_auth(request, org_slug)
    except Exception:
        return _scim_error(401, "Unauthorized")
    pool = request.app.state.pool
    ctx = _scim_ctx(request, pool, org)
    try:
        async with pool.acquire() as conn:
            await _service.delete_group(pool, conn, ctx, group_id=group_id, org_id=org["id"])
    except _errors.NotFoundError as exc:
        return _scim_error(404, str(exc))
    return None

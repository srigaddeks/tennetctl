"""
iam.sessions — FastAPI routes (self-service).

Users see and manage their own sessions only. No cross-user listing in v1 —
that lives behind an admin role check when roles are enforced.

  GET    /v1/sessions           — list my sessions (query: only_valid, limit, offset)
  GET    /v1/sessions/{id}      — fetch my session details
  PATCH  /v1/sessions/{id}      — extend={true} pushes expires_at out
  DELETE /v1/sessions/{id}      — revoke a session (204)
"""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request, Response

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)

SessionRead = _schemas.SessionRead
SessionPatchBody = _schemas.SessionPatchBody

router = APIRouter(prefix="/v1/sessions", tags=["iam.sessions"])


def _require_auth(request: Request) -> tuple[str, str]:
    user_id = getattr(request.state, "user_id", None)
    session_id = getattr(request.state, "session_id", None)
    if not user_id or not session_id:
        raise _errors.UnauthorizedError("not signed in")
    return user_id, session_id


def _vault(request: Request) -> Any:
    vault = getattr(request.app.state, "vault", None)
    if vault is None:
        raise _errors.AppError(
            "VAULT_DISABLED",
            "vault module is not enabled; sessions require vault for signing key",
            status_code=503,
        )
    return vault


def _build_ctx(request: Request, pool: Any, user_id: str, session_id: str) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=user_id,
        session_id=session_id,
        org_id=getattr(request.state, "org_id", None),
        workspace_id=getattr(request.state, "workspace_id", None),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="setup",
        extras={"pool": pool},
    )


@router.get("", status_code=200)
async def list_my_sessions_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    only_valid: bool = False,
) -> dict:
    user_id, _ = _require_auth(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items, total = await _service.list_my_sessions(
            conn, user_id=user_id,
            limit=limit, offset=offset, only_valid=only_valid,
        )
    data = [SessionRead(**row).model_dump() for row in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.get("/{session_id}", status_code=200)
async def get_my_session_route(request: Request, session_id: str) -> dict:
    user_id, _ = _require_auth(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.get_my_session(
            conn, user_id=user_id, session_id=session_id,
        )
    if row is None:
        raise _errors.NotFoundError(f"Session {session_id!r} not found.")
    return _response.success(SessionRead(**row).model_dump())


@router.patch("/{session_id}", status_code=200)
async def patch_my_session_route(
    request: Request, session_id: str, body: SessionPatchBody,
) -> dict:
    user_id, caller_session = _require_auth(request)
    if not body.extend:
        raise _errors.ValidationError(
            "PATCH body currently supports only {extend: true}"
        )
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool, user_id, caller_session)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            updated = await _service.extend_my_session(
                pool, conn, ctx,
                vault_client=vault,
                user_id=user_id, session_id=session_id,
            )
    return _response.success(SessionRead(**updated).model_dump())


@router.delete("/{session_id}", status_code=204)
async def delete_my_session_route(
    request: Request, session_id: str,
) -> Response:
    user_id, caller_session = _require_auth(request)
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, user_id, caller_session)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.revoke_my_session(
                pool, conn, ctx,
                user_id=user_id, session_id=session_id,
            )
    return Response(status_code=204)

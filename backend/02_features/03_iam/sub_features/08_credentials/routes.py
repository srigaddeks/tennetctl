"""
iam.credentials — FastAPI routes (self-service only).

One endpoint: PATCH /v1/credentials/me. The caller must be authenticated AND
must re-prove knowledge of the current password. On success, every other live
session for this user is revoked so a leaked session can't survive a rotation.
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
    "backend.02_features.03_iam.sub_features.08_credentials.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.08_credentials.service"
)

PasswordChangeBody = _schemas.PasswordChangeBody

router = APIRouter(prefix="/v1/credentials", tags=["iam.credentials"])


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
            "vault module is not enabled; credentials ops require vault for pepper access",
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


@router.patch("/me", status_code=200)
async def change_my_password_route(
    request: Request, body: PasswordChangeBody,
) -> Response:
    user_id, session_id = _require_auth(request)
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool, user_id, session_id)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            other_revoked = await _service.change_password(
                pool, conn, ctx,
                vault_client=vault,
                user_id=user_id,
                current_password=body.current_password,
                new_password=body.new_password,
                current_session_id=session_id,
            )
    return _response.success_response(
        {"changed": True, "other_sessions_revoked": other_revoked},
        status_code=200,
    )

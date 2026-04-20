"""FastAPI routes for iam.email_verification."""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_errors: Any = import_module("backend.01_core.errors")
_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.16_email_verification.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.16_email_verification.service"
)

SendVerificationRequest = _schemas.SendVerificationRequest
ConsumeVerificationRequest = _schemas.ConsumeVerificationRequest

router = APIRouter(prefix="/v1/auth/verify-email", tags=["iam.email_verification"])

_DEFAULT_VERIFY_URL_BASE = "/auth/verify-email"


def _build_ctx(request: Request, pool: Any) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=getattr(request.state, "user_id", None),
        session_id=getattr(request.state, "session_id", None),
        org_id=getattr(request.state, "org_id", None),
        workspace_id=None,
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="setup",
        pool=pool,
        extras={"pool": pool},
    )


def _vault(request: Request) -> Any:
    vault = getattr(request.app.state, "vault", None)
    if vault is None:
        raise _errors.AppError("VAULT_DISABLED", "Vault not configured.", 503)
    return vault


@router.post("/send", status_code=202)
async def send_verification_route(body: SendVerificationRequest, request: Request) -> dict:
    """
    Request a verification email for the given email address.
    Always returns 202 — no user enumeration.
    """
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool)
    # Derive verify URL base from request origin
    origin = request.headers.get("origin", "")
    verify_url_base = f"{origin}{_DEFAULT_VERIFY_URL_BASE}" if origin else _DEFAULT_VERIFY_URL_BASE
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.request_verification(
                pool, conn, ctx,
                email=body.email,
                verify_url_base=verify_url_base,
                vault_client=vault,
            )
    return _response.success({"sent": True, "message": "If that email is registered, a verification link is on its way."})


@router.post("/consume", status_code=200)
async def consume_verification_route(body: ConsumeVerificationRequest, request: Request) -> dict:
    """Consume a verification token and mark the user's email as verified."""
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            user = await _service.consume_token(
                pool, conn, ctx,
                raw_token=body.token,
                vault_client=vault,
            )
    return _response.success({"verified": True, "user_id": user.get("id")})

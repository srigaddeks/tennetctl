"""IAM mobile-OTP — FastAPI routes.

Public endpoints (no session required):
  POST /v1/auth/mobile-otp/request
  POST /v1/auth/mobile-otp/verify
"""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any, Annotated
import re

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.30_mobile_otp.service"
)

E164_RE = re.compile(r"^\+\d{7,15}$")


class _MobileOtpRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone_e164: Annotated[str, Field(min_length=8, max_length=16)]

    @field_validator("phone_e164")
    @classmethod
    def _check(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not E164_RE.match(v):
            raise ValueError("phone must be in E.164 format (e.g. +919876543210)")
        return v


class _MobileOtpVerify(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone_e164: Annotated[str, Field(min_length=8, max_length=16)]
    code: Annotated[str, Field(min_length=4, max_length=10)]
    display_name: Annotated[str | None, Field(max_length=120)] = None
    account_type: Annotated[str, Field(max_length=40)] = "soma_delights_customer"

    @field_validator("phone_e164")
    @classmethod
    def _check_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if not E164_RE.match(v):
            raise ValueError("phone must be in E.164 format")
        return v

    @field_validator("code")
    @classmethod
    def _check_code(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("code must be numeric")
        return v


router = APIRouter(tags=["iam.mobile_otp"])


def _ctx(request: Request, pool: Any, *, audit_category: str) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=getattr(request.state, "user_id", None),
        session_id=getattr(request.state, "session_id", None),
        org_id=getattr(request.state, "org_id", None),
        workspace_id=getattr(request.state, "workspace_id", None),
        application_id=getattr(request.state, "application_id", None),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category=audit_category,
        pool=pool,
    )


@router.post("/v1/auth/mobile-otp/request", status_code=200)
async def request_mobile_otp_route(
    request: Request, body: _MobileOtpRequest,
) -> dict:
    pool = request.app.state.pool
    vault = request.app.state.vault
    ctx = _ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx2 = replace(ctx, conn=conn)
            result = await _service.request_mobile_otp(
                pool, conn, ctx2,
                phone_e164=body.phone_e164,
                vault_client=vault,
            )
    payload: dict[str, Any] = {
        "sent": True,
        "message": "Code sent. Enter it within 5 minutes.",
    }
    # Only echo debug_code in stub mode (dev). Never in real Twilio mode.
    if result.get("debug_code") is not None:
        payload["debug_code"] = result["debug_code"]
    return _response.success(payload)


@router.post("/v1/auth/mobile-otp/verify", status_code=200)
async def verify_mobile_otp_route(
    request: Request, body: _MobileOtpVerify,
) -> dict:
    pool = request.app.state.pool
    vault = request.app.state.vault
    ctx = _ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx2 = replace(ctx, conn=conn)
            result = await _service.verify_mobile_otp(
                pool, conn, ctx2,
                phone_e164=body.phone_e164,
                code=body.code,
                account_type=body.account_type,
                display_name=body.display_name,
                vault_client=vault,
                request=request,
            )
    return _response.success(result)

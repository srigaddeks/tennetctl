from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request, status

from ..schemas import TokenPairResponse
from ..dependencies import get_client_ip
from .dependencies import get_passwordless_service
from .schemas import RequestMagicLinkRequest, RequestMagicLinkResponse
from .service import PasswordlessService

_telemetry_module = import_module("backend.01_core.telemetry")
InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter

router = InstrumentedAPIRouter(prefix="/api/v1/auth/passwordless", tags=["auth-passwordless"])


@router.post("/request", response_model=RequestMagicLinkResponse)
async def request_magic_link(
    payload: RequestMagicLinkRequest,
    request: Request,
    service: Annotated[PasswordlessService, Depends(get_passwordless_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)],
) -> RequestMagicLinkResponse:
    return await service.request_magic_link(
        payload,
        client_ip=client_ip,
        request_id=request.headers.get("X-Request-ID"),
    )


@router.post("/request-assignee", response_model=RequestMagicLinkResponse)
async def request_assignee_magic_link(
    payload: RequestMagicLinkRequest,
    request: Request,
    service: Annotated[PasswordlessService, Depends(get_passwordless_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)],
) -> RequestMagicLinkResponse:
    return await service.request_assignee_magic_link(
        payload,
        client_ip=client_ip,
        request_id=request.headers.get("X-Request-ID"),
    )


@router.post("/verify", response_model=TokenPairResponse)
async def verify_magic_link(
    request: Request,
    service: Annotated[PasswordlessService, Depends(get_passwordless_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)],
    token: Annotated[str, Query(min_length=10, max_length=512)],
) -> TokenPairResponse:
    return await service.verify_magic_link(
        token,
        client_ip=client_ip,
        user_agent=request.headers.get("User-Agent"),
        request_id=request.headers.get("X-Request-ID"),
    )

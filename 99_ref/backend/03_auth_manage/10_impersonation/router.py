from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Request

from ..dependencies import get_client_ip, get_current_access_claims, require_not_api_key
from .dependencies import get_impersonation_service
from .schemas import (
    EndImpersonationResponse,
    ImpersonationStatusResponse,
    StartImpersonationRequest,
    StartImpersonationResponse,
)
from .service import ImpersonationService

_telemetry_module = import_module("backend.01_core.telemetry")
InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter

router = InstrumentedAPIRouter(prefix="/api/v1/am/impersonation", tags=["impersonation"])


@router.post("/start", response_model=StartImpersonationResponse)
async def start_impersonation(
    payload: StartImpersonationRequest,
    request: Request,
    service: Annotated[ImpersonationService, Depends(get_impersonation_service)],
    claims=Depends(require_not_api_key),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> StartImpersonationResponse:
    return await service.start_impersonation(
        payload,
        admin_claims=claims,
        client_ip=client_ip,
        user_agent=request.headers.get("user-agent"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/end", response_model=EndImpersonationResponse)
async def end_impersonation(
    request: Request,
    service: Annotated[ImpersonationService, Depends(get_impersonation_service)],
    claims=Depends(require_not_api_key),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> EndImpersonationResponse:
    return await service.end_impersonation(
        claims=claims,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/status", response_model=ImpersonationStatusResponse)
async def impersonation_status(
    service: Annotated[ImpersonationService, Depends(get_impersonation_service)],
    claims=Depends(require_not_api_key),
) -> ImpersonationStatusResponse:
    return service.get_impersonation_status(claims)

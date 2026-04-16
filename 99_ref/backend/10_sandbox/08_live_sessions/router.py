from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_live_session_service
from .schemas import (
    AttachSignalRequest,
    AttachThreatRequest,
    LiveSessionListResponse,
    LiveSessionResponse,
    SaveDatasetRequest,
    SaveDatasetResponse,
    StartSessionRequest,
    StreamResponse,
)
from .service import LiveSessionService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/live-sessions", tags=["sandbox-live-sessions"])


@router.post("", response_model=LiveSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    body: StartSessionRequest,
    service: Annotated[LiveSessionService, Depends(get_live_session_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> LiveSessionResponse:
    return await service.start_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=body,
    )


@router.get("", response_model=LiveSessionListResponse)
async def list_sessions(
    service: Annotated[LiveSessionService, Depends(get_live_session_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str | None = Query(default=None),
    session_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> LiveSessionListResponse:
    return await service.list_sessions(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        session_status=session_status,
        limit=limit,
        offset=offset,
    )


@router.get("/{session_id}", response_model=LiveSessionResponse)
async def get_session(
    session_id: str,
    service: Annotated[LiveSessionService, Depends(get_live_session_service)],
    claims=Depends(get_current_access_claims),
) -> LiveSessionResponse:
    return await service.get_session(
        user_id=claims.subject, session_id=session_id,
    )


@router.get("/{session_id}/stream", response_model=StreamResponse)
async def get_stream(
    session_id: str,
    service: Annotated[LiveSessionService, Depends(get_live_session_service)],
    claims=Depends(get_current_access_claims),
    after_sequence: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> StreamResponse:
    return await service.get_stream(
        user_id=claims.subject,
        session_id=session_id,
        after_sequence=after_sequence,
        limit=limit,
    )


@router.post("/{session_id}/pause", response_model=LiveSessionResponse)
async def pause_session(
    session_id: str,
    service: Annotated[LiveSessionService, Depends(get_live_session_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> LiveSessionResponse:
    return await service.pause_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        session_id=session_id,
    )


@router.post("/{session_id}/resume", response_model=LiveSessionResponse)
async def resume_session(
    session_id: str,
    service: Annotated[LiveSessionService, Depends(get_live_session_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> LiveSessionResponse:
    return await service.resume_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        session_id=session_id,
    )


@router.post("/{session_id}/stop", response_model=LiveSessionResponse)
async def stop_session(
    session_id: str,
    service: Annotated[LiveSessionService, Depends(get_live_session_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> LiveSessionResponse:
    return await service.stop_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        session_id=session_id,
    )


@router.post("/{session_id}/attach-signal", response_model=LiveSessionResponse)
async def attach_signal(
    session_id: str,
    body: AttachSignalRequest,
    service: Annotated[LiveSessionService, Depends(get_live_session_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> LiveSessionResponse:
    return await service.attach_signal(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        session_id=session_id,
        request=body,
    )


@router.post("/{session_id}/detach-signal", response_model=LiveSessionResponse)
async def detach_signal(
    session_id: str,
    body: AttachSignalRequest,
    service: Annotated[LiveSessionService, Depends(get_live_session_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> LiveSessionResponse:
    return await service.detach_signal(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        session_id=session_id,
        request=body,
    )


@router.post("/{session_id}/attach-threat", response_model=LiveSessionResponse)
async def attach_threat(
    session_id: str,
    body: AttachThreatRequest,
    service: Annotated[LiveSessionService, Depends(get_live_session_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> LiveSessionResponse:
    return await service.attach_threat(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        session_id=session_id,
        request=body,
    )


@router.post("/{session_id}/detach-threat", response_model=LiveSessionResponse)
async def detach_threat(
    session_id: str,
    body: AttachThreatRequest,
    service: Annotated[LiveSessionService, Depends(get_live_session_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> LiveSessionResponse:
    return await service.detach_threat(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        session_id=session_id,
        request=body,
    )


@router.post("/{session_id}/save-dataset", response_model=SaveDatasetResponse)
async def save_dataset(
    session_id: str,
    body: SaveDatasetRequest,
    service: Annotated[LiveSessionService, Depends(get_live_session_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> SaveDatasetResponse:
    return await service.save_dataset(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        session_id=session_id,
        request=body,
    )

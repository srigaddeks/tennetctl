from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request, status

from .dependencies import get_ssf_transmitter_service
from .schemas import (
    AddSubjectRequest,
    CreateStreamRequest,
    PollResponse,
    StreamListResponse,
    StreamResponse,
    SubjectResponse,
    UpdateStreamRequest,
    UpdateStreamStatusRequest,
    VerifyResponse,
)
from .service import SSFTransmitterService
from .transmitter_config import get_transmitter_config

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/ssf", tags=["sandbox-ssf-transmitter"])

# Well-known router — mounted at app root (outside /sb prefix)
wellknown_router = InstrumentedAPIRouter(tags=["ssf-discovery"])


# ── Well-known discovery endpoint (public, no auth) ─────────────────────

@wellknown_router.get("/.well-known/ssf-configuration")
async def ssf_configuration(request: Request) -> dict:
    base_url = str(request.base_url).rstrip("/")
    return get_transmitter_config(base_url)


# ── Stream management ───────────────────────────────────────────────────

@router.post("/streams", response_model=StreamResponse, status_code=status.HTTP_201_CREATED)
async def create_stream(
    body: CreateStreamRequest,
    service: Annotated[SSFTransmitterService, Depends(get_ssf_transmitter_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> StreamResponse:
    return await service.create_stream(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=body,
    )


@router.get("/streams", response_model=StreamListResponse)
async def list_streams(
    service: Annotated[SSFTransmitterService, Depends(get_ssf_transmitter_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> StreamListResponse:
    return await service.list_streams(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        limit=limit,
        offset=offset,
    )


@router.get("/streams/{stream_id}", response_model=StreamResponse)
async def get_stream(
    stream_id: str,
    service: Annotated[SSFTransmitterService, Depends(get_ssf_transmitter_service)],
    claims=Depends(get_current_access_claims),
) -> StreamResponse:
    return await service.get_stream(
        user_id=claims.subject, stream_id=stream_id
    )


@router.patch("/streams/{stream_id}", response_model=StreamResponse)
async def update_stream(
    stream_id: str,
    body: UpdateStreamRequest,
    service: Annotated[SSFTransmitterService, Depends(get_ssf_transmitter_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> StreamResponse:
    return await service.update_stream(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        stream_id=stream_id,
        request=body,
    )


@router.delete("/streams/{stream_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stream(
    stream_id: str,
    service: Annotated[SSFTransmitterService, Depends(get_ssf_transmitter_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    await service.delete_stream(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        stream_id=stream_id,
    )


# ── Stream status ───────────────────────────────────────────────────────

@router.get("/streams/{stream_id}/status")
async def get_stream_status(
    stream_id: str,
    service: Annotated[SSFTransmitterService, Depends(get_ssf_transmitter_service)],
    claims=Depends(get_current_access_claims),
) -> dict:
    return await service.get_stream_status(
        user_id=claims.subject, stream_id=stream_id
    )


@router.patch("/streams/{stream_id}/status")
async def update_stream_status(
    stream_id: str,
    body: UpdateStreamStatusRequest,
    service: Annotated[SSFTransmitterService, Depends(get_ssf_transmitter_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> dict:
    return await service.update_stream_status(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        stream_id=stream_id,
        request=body,
    )


# ── Subjects ────────────────────────────────────────────────────────────

@router.post("/streams/{stream_id}/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def add_subject(
    stream_id: str,
    body: AddSubjectRequest,
    service: Annotated[SSFTransmitterService, Depends(get_ssf_transmitter_service)],
    claims=Depends(get_current_access_claims),
) -> SubjectResponse:
    return await service.add_subject(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        stream_id=stream_id,
        request=body,
    )


@router.delete("/streams/{stream_id}/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_subject(
    stream_id: str,
    subject_id: str,
    service: Annotated[SSFTransmitterService, Depends(get_ssf_transmitter_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.remove_subject(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        stream_id=stream_id,
        subject_id=subject_id,
    )


# ── Verification ────────────────────────────────────────────────────────

@router.post("/streams/{stream_id}/verify", response_model=VerifyResponse)
async def verify_stream(
    stream_id: str,
    service: Annotated[SSFTransmitterService, Depends(get_ssf_transmitter_service)],
    claims=Depends(get_current_access_claims),
) -> VerifyResponse:
    return await service.verify_stream(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        stream_id=stream_id,
    )


# ── Poll endpoint ───────────────────────────────────────────────────────

@router.get("/poll/{stream_id}", response_model=PollResponse)
async def poll_sets(
    stream_id: str,
    service: Annotated[SSFTransmitterService, Depends(get_ssf_transmitter_service)],
    claims=Depends(get_current_access_claims),
    acks: str | None = Query(default=None, description="Comma-separated JTIs to acknowledge"),
    limit: int = Query(default=25, ge=1, le=100),
) -> PollResponse:
    ack_list = [a.strip() for a in acks.split(",") if a.strip()] if acks else None
    return await service.poll_sets(
        user_id=claims.subject,
        stream_id=stream_id,
        acks=ack_list,
        limit=limit,
    )

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_release_incident_service
from .service import ReleaseIncidentService
from ..schemas import (
    CreateIncidentRequest,
    CreateIncidentUpdateRequest,
    CreateReleaseRequest,
    IncidentListResponse,
    IncidentResponse,
    ReleaseListResponse,
    ReleaseResponse,
    UpdateIncidentRequest,
    UpdateReleaseRequest,
)

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/notifications", tags=["notification-releases"])


# ------------------------------------------------------------------ #
# Releases
# ------------------------------------------------------------------ #


@router.get("/releases", response_model=ReleaseListResponse)
async def list_releases(
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = Query(default=None, alias="status"),
) -> ReleaseListResponse:
    return await service.list_releases(
        user_id=claims.subject, tenant_key=claims.tenant_key,
        limit=limit, offset=offset, status=status_filter,
    )


@router.get("/releases/public", response_model=ReleaseListResponse)
async def list_published_releases(
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ReleaseListResponse:
    """List published releases — no platform permission required."""
    return await service.list_published_releases(
        tenant_key=claims.tenant_key, limit=limit, offset=offset,
    )


@router.get("/releases/{release_id}", response_model=ReleaseResponse)
async def get_release(
    release_id: str,
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
) -> ReleaseResponse:
    return await service.get_release(user_id=claims.subject, release_id=release_id)


@router.post(
    "/releases",
    response_model=ReleaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_release(
    body: CreateReleaseRequest,
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
) -> ReleaseResponse:
    return await service.create_release(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body,
    )


@router.patch("/releases/{release_id}", response_model=ReleaseResponse)
async def update_release(
    release_id: str,
    body: UpdateReleaseRequest,
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
) -> ReleaseResponse:
    return await service.update_release(
        user_id=claims.subject, release_id=release_id, request=body,
    )


@router.post("/releases/{release_id}/publish", response_model=ReleaseResponse)
async def publish_release(
    release_id: str,
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
    notify: bool = Query(default=True),
) -> ReleaseResponse:
    return await service.publish_release(
        user_id=claims.subject, tenant_key=claims.tenant_key,
        release_id=release_id, notify_users=notify,
    )


@router.post("/releases/{release_id}/archive", response_model=ReleaseResponse)
async def archive_release(
    release_id: str,
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
) -> ReleaseResponse:
    return await service.archive_release(user_id=claims.subject, release_id=release_id)


# ------------------------------------------------------------------ #
# Incidents
# ------------------------------------------------------------------ #


@router.get("/incidents", response_model=IncidentListResponse)
async def list_incidents(
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = Query(default=None, alias="status"),
) -> IncidentListResponse:
    return await service.list_incidents(
        user_id=claims.subject, tenant_key=claims.tenant_key,
        limit=limit, offset=offset, status=status_filter,
    )


@router.get("/incidents/active", response_model=IncidentListResponse)
async def list_active_incidents(
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> IncidentListResponse:
    """List non-resolved incidents — no platform permission required."""
    return await service.list_active_incidents(
        tenant_key=claims.tenant_key, limit=limit, offset=offset,
    )


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
) -> IncidentResponse:
    return await service.get_incident(user_id=claims.subject, incident_id=incident_id)


@router.post(
    "/incidents",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_incident(
    body: CreateIncidentRequest,
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
) -> IncidentResponse:
    return await service.create_incident(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body,
    )


@router.patch("/incidents/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    body: UpdateIncidentRequest,
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
) -> IncidentResponse:
    return await service.update_incident(
        user_id=claims.subject, incident_id=incident_id, request=body,
    )


@router.post("/incidents/{incident_id}/updates", response_model=IncidentResponse)
async def post_incident_update(
    incident_id: str,
    body: CreateIncidentUpdateRequest,
    service: Annotated[ReleaseIncidentService, Depends(get_release_incident_service)],
    claims=Depends(get_current_access_claims),
) -> IncidentResponse:
    return await service.post_incident_update(
        user_id=claims.subject, tenant_key=claims.tenant_key,
        incident_id=incident_id, request=body,
    )



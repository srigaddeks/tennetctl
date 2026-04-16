from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_threat_type_service
from .schemas import (
    CreateThreatTypeRequest,
    SimulateThreatRequest,
    SimulateThreatResponse,
    ThreatTypeListResponse,
    ThreatTypeResponse,
    UpdateThreatTypeRequest,
)
from .service import ThreatTypeService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/threat-types", tags=["sandbox-threat-types"])


@router.get("", response_model=ThreatTypeListResponse)
async def list_threat_types(
    service: Annotated[ThreatTypeService, Depends(get_threat_type_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str | None = Query(default=None),
    severity_code: str | None = Query(default=None),
    search: str | None = Query(default=None),
    sort_by: str = Query(default="threat_code"),
    sort_dir: str = Query(default="asc"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> ThreatTypeListResponse:
    return await service.list_threat_types(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        severity_code=severity_code,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


@router.get("/{threat_type_id}", response_model=ThreatTypeResponse)
async def get_threat_type(
    threat_type_id: str,
    service: Annotated[ThreatTypeService, Depends(get_threat_type_service)],
    claims=Depends(get_current_access_claims),
) -> ThreatTypeResponse:
    return await service.get_threat_type(
        user_id=claims.subject, threat_type_id=threat_type_id
    )


@router.post("", response_model=ThreatTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_threat_type(
    body: CreateThreatTypeRequest,
    service: Annotated[ThreatTypeService, Depends(get_threat_type_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> ThreatTypeResponse:
    return await service.create_threat_type(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=body,
    )


@router.patch("/{threat_type_id}", response_model=ThreatTypeResponse)
async def update_threat_type(
    threat_type_id: str,
    body: UpdateThreatTypeRequest,
    service: Annotated[ThreatTypeService, Depends(get_threat_type_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> ThreatTypeResponse:
    return await service.update_threat_type(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        threat_type_id=threat_type_id,
        request=body,
    )


@router.delete("/{threat_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_threat_type(
    threat_type_id: str,
    service: Annotated[ThreatTypeService, Depends(get_threat_type_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    await service.delete_threat_type(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        threat_type_id=threat_type_id,
    )


@router.post("/{threat_type_id}/simulate", response_model=SimulateThreatResponse)
async def simulate_threat(
    threat_type_id: str,
    body: SimulateThreatRequest,
    service: Annotated[ThreatTypeService, Depends(get_threat_type_service)],
    claims=Depends(get_current_access_claims),
) -> SimulateThreatResponse:
    return await service.simulate_threat(
        user_id=claims.subject,
        threat_type_id=threat_type_id,
        request=body,
    )


@router.get("/{threat_type_id}/versions", response_model=list[ThreatTypeResponse])
async def list_versions(
    threat_type_id: str,
    service: Annotated[ThreatTypeService, Depends(get_threat_type_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> list[ThreatTypeResponse]:
    return await service.list_versions(
        user_id=claims.subject,
        threat_type_id=threat_type_id,
        org_id=org_id,
    )


@router.get("/{threat_type_id}/evaluations", response_model=list)
async def list_evaluations(
    threat_type_id: str,
    service: Annotated[ThreatTypeService, Depends(get_threat_type_service)],
    claims=Depends(get_current_access_claims),
) -> list:
    """Evaluation history — stub endpoint for future implementation."""
    return []

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Request, status

from .dependencies import get_license_profile_service
from .schemas import (
    BatchSetProfileSettingsRequest,
    CreateLicenseProfileRequest,
    LicenseProfileListResponse,
    LicenseProfileResponse,
    LicenseProfileSettingResponse,
    SetProfileSettingRequest,
    UpdateLicenseProfileRequest,
)
from .service import LicenseProfileService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/am/license-profiles", tags=["access-management"])


@router.get("", response_model=LicenseProfileListResponse)
async def list_profiles(
    service: Annotated[LicenseProfileService, Depends(get_license_profile_service)],
    claims=Depends(get_current_access_claims),
) -> LicenseProfileListResponse:
    return await service.list_profiles(actor_id=claims.subject)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LicenseProfileResponse)
async def create_profile(
    payload: CreateLicenseProfileRequest,
    request: Request,
    service: Annotated[LicenseProfileService, Depends(get_license_profile_service)],
    claims=Depends(get_current_access_claims),
) -> LicenseProfileResponse:
    return await service.create_profile(
        payload, actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
    )


@router.patch("/{code}", response_model=LicenseProfileResponse)
async def update_profile(
    code: str,
    payload: UpdateLicenseProfileRequest,
    request: Request,
    service: Annotated[LicenseProfileService, Depends(get_license_profile_service)],
    claims=Depends(get_current_access_claims),
) -> LicenseProfileResponse:
    return await service.update_profile(
        code, payload, actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
    )


@router.put("/{code}/settings/{key}", response_model=LicenseProfileSettingResponse)
async def set_profile_setting(
    code: str,
    key: str,
    payload: SetProfileSettingRequest,
    request: Request,
    service: Annotated[LicenseProfileService, Depends(get_license_profile_service)],
    claims=Depends(get_current_access_claims),
) -> LicenseProfileSettingResponse:
    return await service.set_setting(
        code, key, payload.value, actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
    )


@router.delete("/{code}/settings/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_setting(
    code: str,
    key: str,
    request: Request,
    service: Annotated[LicenseProfileService, Depends(get_license_profile_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_setting(
        code, key, actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
    )

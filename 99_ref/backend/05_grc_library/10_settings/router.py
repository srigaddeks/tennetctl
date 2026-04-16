from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, status

from .dependencies import get_framework_setting_service
from .schemas import (
    FrameworkSettingListResponse,
    FrameworkSettingResponse,
    SetFrameworkSettingRequest,
)
from .service import FrameworkSettingService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/fr", tags=["grc-settings"])


@router.get("/frameworks/{framework_id}/settings", response_model=FrameworkSettingListResponse)
async def list_framework_settings(
    framework_id: str,
    service: Annotated[FrameworkSettingService, Depends(get_framework_setting_service)],
    claims=Depends(get_current_access_claims),
) -> FrameworkSettingListResponse:
    return await service.list_settings(user_id=claims.subject, framework_id=framework_id)


@router.put("/frameworks/{framework_id}/settings/{setting_key}", response_model=FrameworkSettingResponse)
async def set_framework_setting(
    framework_id: str,
    setting_key: str,
    body: SetFrameworkSettingRequest,
    service: Annotated[FrameworkSettingService, Depends(get_framework_setting_service)],
    claims=Depends(get_current_access_claims),
) -> FrameworkSettingResponse:
    return await service.set_setting(
        user_id=claims.subject, tenant_key=claims.tenant_key,
        framework_id=framework_id, setting_key=setting_key, request=body
    )


@router.delete("/frameworks/{framework_id}/settings/{setting_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_framework_setting(
    framework_id: str,
    setting_key: str,
    service: Annotated[FrameworkSettingService, Depends(get_framework_setting_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_setting(
        user_id=claims.subject, tenant_key=claims.tenant_key,
        framework_id=framework_id, setting_key=setting_key
    )

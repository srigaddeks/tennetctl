"""Generic entity settings router — 5 endpoints serve all entity types.

Valid entity_type values: org, workspace, role, group, feature, product
"""

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Request, status

_telemetry_mod = import_module("backend.01_core.telemetry")
_deps = import_module("backend.03_auth_manage.dependencies")
_settings_deps = import_module("backend.03_auth_manage.12_entity_settings.dependencies")
_schemas = import_module("backend.03_auth_manage.12_entity_settings.schemas")

InstrumentedAPIRouter = _telemetry_mod.InstrumentedAPIRouter
get_current_access_claims = _deps.get_current_access_claims
get_entity_settings_service = _settings_deps.get_entity_settings_service
EntitySettingsService = _settings_deps.EntitySettingsService

SettingResponse = _schemas.SettingResponse
SettingListResponse = _schemas.SettingListResponse
SetSettingRequest = _schemas.SetSettingRequest
BatchSetSettingsRequest = _schemas.BatchSetSettingsRequest
BatchSetSettingsResponse = _schemas.BatchSetSettingsResponse
SettingKeyListResponse = _schemas.SettingKeyListResponse

router = InstrumentedAPIRouter(prefix="/api/v1/am/settings", tags=["entity-settings"])


@router.get("/{entity_type}/{entity_id}", response_model=SettingListResponse)
async def list_settings(
    entity_type: str,
    entity_id: str,
    service: Annotated[EntitySettingsService, Depends(get_entity_settings_service)],
    claims=Depends(get_current_access_claims),
) -> SettingListResponse:
    return await service.list_settings(
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=claims.subject,
    )


@router.get("/{entity_type}/{entity_id}/keys", response_model=SettingKeyListResponse)
async def list_setting_keys(
    entity_type: str,
    entity_id: str,
    service: Annotated[EntitySettingsService, Depends(get_entity_settings_service)],
    claims=Depends(get_current_access_claims),
) -> SettingKeyListResponse:
    return await service.list_setting_keys(
        entity_type=entity_type,
        actor_id=claims.subject,
    )


@router.put("/{entity_type}/{entity_id}/{key}", response_model=SettingResponse)
async def set_setting(
    entity_type: str,
    entity_id: str,
    key: str,
    body: SetSettingRequest,
    request: Request,
    service: Annotated[EntitySettingsService, Depends(get_entity_settings_service)],
    claims=Depends(get_current_access_claims),
) -> SettingResponse:
    return await service.set_setting(
        entity_type=entity_type,
        entity_id=entity_id,
        setting_key=key,
        setting_value=body.value,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
    )


@router.put("/{entity_type}/{entity_id}", response_model=BatchSetSettingsResponse)
async def batch_set_settings(
    entity_type: str,
    entity_id: str,
    body: BatchSetSettingsRequest,
    request: Request,
    service: Annotated[EntitySettingsService, Depends(get_entity_settings_service)],
    claims=Depends(get_current_access_claims),
) -> BatchSetSettingsResponse:
    return await service.batch_set_settings(
        entity_type=entity_type,
        entity_id=entity_id,
        settings=body.settings,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
    )


@router.delete(
    "/{entity_type}/{entity_id}/{key}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_setting(
    entity_type: str,
    entity_id: str,
    key: str,
    request: Request,
    service: Annotated[EntitySettingsService, Depends(get_entity_settings_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_setting(
        entity_type=entity_type,
        entity_id=entity_id,
        setting_key=key,
        actor_id=claims.subject,
        client_ip=request.client.host if request.client else None,
        session_id=claims.session_id,
    )

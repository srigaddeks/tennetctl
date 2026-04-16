from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends

from .dependencies import get_provider_service
from .schemas import (
    ProviderDefinitionSchema,
    ProviderListResponse,
    ProviderVersionSchema,
)
from .service import ProviderService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/providers", tags=["asset-providers"])


@router.get("", response_model=ProviderListResponse)
async def list_providers(
    service: Annotated[ProviderService, Depends(get_provider_service)],
    claims=Depends(get_current_access_claims),
) -> ProviderListResponse:
    return await service.list_providers(user_id=claims.subject)


@router.get("/{code}", response_model=ProviderDefinitionSchema)
async def get_provider(
    code: str,
    service: Annotated[ProviderService, Depends(get_provider_service)],
    claims=Depends(get_current_access_claims),
) -> ProviderDefinitionSchema:
    return await service.get_provider(user_id=claims.subject, code=code)


@router.get("/{code}/versions", response_model=list[ProviderVersionSchema])
async def list_provider_versions(
    code: str,
    service: Annotated[ProviderService, Depends(get_provider_service)],
    claims=Depends(get_current_access_claims),
) -> list[ProviderVersionSchema]:
    return await service.list_provider_versions(
        user_id=claims.subject, provider_code=code
    )

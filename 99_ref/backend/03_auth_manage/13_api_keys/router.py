from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Response, status

from .dependencies import get_api_key_service
from .schemas import (
    ApiKeyCreatedResponse,
    ApiKeyListResponse,
    ApiKeyResponse,
    CreateApiKeyRequest,
    RevokeApiKeyRequest,
)
from .service import ApiKeyService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
require_not_api_key = _auth_deps_module.require_not_api_key
require_not_impersonating = _auth_deps_module.require_not_impersonating

router = InstrumentedAPIRouter(prefix="/api/v1/am", tags=["api-keys"])


@router.post(
    "/api-keys",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    request: CreateApiKeyRequest,
    service: Annotated[ApiKeyService, Depends(get_api_key_service)],
    claims=Depends(require_not_api_key),
    _impersonation=Depends(require_not_impersonating),
) -> ApiKeyCreatedResponse:
    return await service.create_api_key(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=request,
    )


@router.get("/api-keys", response_model=ApiKeyListResponse)
async def list_api_keys(
    service: Annotated[ApiKeyService, Depends(get_api_key_service)],
    claims=Depends(require_not_api_key),
    _impersonation=Depends(require_not_impersonating),
) -> ApiKeyListResponse:
    return await service.list_api_keys(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
    )


@router.get("/api-keys/{key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    key_id: str,
    service: Annotated[ApiKeyService, Depends(get_api_key_service)],
    claims=Depends(require_not_api_key),
    _impersonation=Depends(require_not_impersonating),
) -> ApiKeyResponse:
    return await service.get_api_key(
        user_id=claims.subject,
        key_id=key_id,
    )


@router.post("/api-keys/{key_id}/rotate", response_model=ApiKeyCreatedResponse)
async def rotate_api_key(
    key_id: str,
    service: Annotated[ApiKeyService, Depends(get_api_key_service)],
    claims=Depends(require_not_api_key),
    _impersonation=Depends(require_not_impersonating),
) -> ApiKeyCreatedResponse:
    return await service.rotate_api_key(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        key_id=key_id,
    )


@router.patch("/api-keys/{key_id}/revoke", response_model=ApiKeyResponse)
async def revoke_api_key(
    key_id: str,
    request: RevokeApiKeyRequest,
    service: Annotated[ApiKeyService, Depends(get_api_key_service)],
    claims=Depends(require_not_api_key),
    _impersonation=Depends(require_not_impersonating),
) -> ApiKeyResponse:
    return await service.revoke_api_key(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        key_id=key_id,
        request=request,
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    service: Annotated[ApiKeyService, Depends(get_api_key_service)],
    claims=Depends(require_not_api_key),
    _impersonation=Depends(require_not_impersonating),
) -> Response:
    await service.delete_api_key(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        key_id=key_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

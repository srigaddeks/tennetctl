from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_library_service
from .schemas import (
    AddConnectorTypeMappingRequest,
    AddPolicyRequest,
    CreateLibraryRequest,
    LibraryListResponse,
    LibraryPolicyResponse,
    LibraryResponse,
    RecommendedLibraryResponse,
    UpdateLibraryRequest,
)
from .service import LibraryService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/libraries", tags=["sandbox-libraries"])


@router.get("", response_model=LibraryListResponse)
async def list_libraries(
    service: Annotated[LibraryService, Depends(get_library_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    library_type_code: str | None = Query(default=None),
    is_published: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> LibraryListResponse:
    return await service.list_libraries(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        library_type_code=library_type_code,
        is_published=is_published,
        limit=limit,
        offset=offset,
    )


@router.get("/{library_id}", response_model=LibraryResponse)
async def get_library(
    library_id: str,
    service: Annotated[LibraryService, Depends(get_library_service)],
    claims=Depends(get_current_access_claims),
) -> LibraryResponse:
    return await service.get_library(
        user_id=claims.subject, library_id=library_id,
    )


@router.post("", response_model=LibraryResponse, status_code=status.HTTP_201_CREATED)
async def create_library(
    body: CreateLibraryRequest,
    service: Annotated[LibraryService, Depends(get_library_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> LibraryResponse:
    return await service.create_library(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=body,
    )


@router.patch("/{library_id}", response_model=LibraryResponse)
async def update_library(
    library_id: str,
    body: UpdateLibraryRequest,
    service: Annotated[LibraryService, Depends(get_library_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> LibraryResponse:
    return await service.update_library(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        library_id=library_id,
        request=body,
    )


@router.delete("/{library_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_library(
    library_id: str,
    service: Annotated[LibraryService, Depends(get_library_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    await service.delete_library(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        library_id=library_id,
    )


@router.post("/{library_id}/publish", response_model=LibraryResponse)
async def publish_library(
    library_id: str,
    service: Annotated[LibraryService, Depends(get_library_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> LibraryResponse:
    return await service.publish_library(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        library_id=library_id,
    )


@router.post("/{library_id}/clone", response_model=LibraryResponse, status_code=status.HTTP_201_CREATED)
async def clone_library(
    library_id: str,
    service: Annotated[LibraryService, Depends(get_library_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> LibraryResponse:
    return await service.clone_library(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        library_id=library_id,
    )


@router.post(
    "/{library_id}/policies",
    response_model=list[LibraryPolicyResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_policy(
    library_id: str,
    body: AddPolicyRequest,
    service: Annotated[LibraryService, Depends(get_library_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> list[LibraryPolicyResponse]:
    return await service.add_policy(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        library_id=library_id,
        request=body,
    )


@router.delete(
    "/{library_id}/policies/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_policy(
    library_id: str,
    policy_id: str,
    service: Annotated[LibraryService, Depends(get_library_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    await service.remove_policy(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        library_id=library_id,
        policy_id=policy_id,
    )


@router.post(
    "/{library_id}/connector-types",
    status_code=status.HTTP_201_CREATED,
)
async def add_connector_type_mapping(
    library_id: str,
    body: AddConnectorTypeMappingRequest,
    service: Annotated[LibraryService, Depends(get_library_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    await service.add_connector_type_mapping(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        library_id=library_id,
        request=body,
    )

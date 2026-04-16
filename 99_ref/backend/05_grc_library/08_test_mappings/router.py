from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, status

from .dependencies import get_test_mapping_service
from .schemas import (
    CreateTestMappingRequest,
    TestMappingListResponse,
    TestMappingResponse,
)
from .service import TestMappingService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/fr", tags=["grc-test-mappings"])


@router.get("/tests/{test_id}/controls", response_model=TestMappingListResponse)
async def list_test_control_mappings(
    test_id: str,
    service: Annotated[TestMappingService, Depends(get_test_mapping_service)],
    claims=Depends(get_current_access_claims),
) -> TestMappingListResponse:
    return await service.list_mappings(user_id=claims.subject, test_id=test_id)


@router.post("/tests/{test_id}/controls", response_model=TestMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_test_control_mapping(
    test_id: str,
    body: CreateTestMappingRequest,
    service: Annotated[TestMappingService, Depends(get_test_mapping_service)],
    claims=Depends(get_current_access_claims),
) -> TestMappingResponse:
    return await service.create_mapping(
        user_id=claims.subject, tenant_key=claims.tenant_key, test_id=test_id, request=body
    )


@router.delete("/tests/{test_id}/controls/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_control_mapping(
    test_id: str,
    mapping_id: str,
    service: Annotated[TestMappingService, Depends(get_test_mapping_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_mapping(
        user_id=claims.subject, tenant_key=claims.tenant_key, test_id=test_id, mapping_id=mapping_id
    )

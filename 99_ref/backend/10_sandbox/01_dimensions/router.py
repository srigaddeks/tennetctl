from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query

from .dependencies import get_sandbox_dimension_service
from .schemas import SandboxDimensionResponse, AssetVersionResponse, ConnectorConfigSchemaResponse
from .service import SandboxDimensionService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_library_deps_module = import_module("backend.10_sandbox.09_libraries.dependencies")
_library_schemas_module = import_module("backend.10_sandbox.09_libraries.schemas")
_library_service_module = import_module("backend.10_sandbox.09_libraries.service")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
get_library_service = _library_deps_module.get_library_service
RecommendedLibraryResponse = _library_schemas_module.RecommendedLibraryResponse
LibraryService = _library_service_module.LibraryService

router = InstrumentedAPIRouter(prefix="/api/v1/sb/dimensions", tags=["sandbox-dimensions"])


@router.get("/stats")
async def get_sandbox_stats(
    service: Annotated[SandboxDimensionService, Depends(get_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
):
    return await service.get_sandbox_stats(user_id=claims.subject, org_id=org_id)


@router.get("/connector-categories", response_model=list[SandboxDimensionResponse])
async def list_connector_categories(
    service: Annotated[SandboxDimensionService, Depends(get_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[SandboxDimensionResponse]:
    return await service.list_dimension(dimension_name="connector_categories")


@router.get("/connector-types", response_model=list[SandboxDimensionResponse])
async def list_connector_types(
    service: Annotated[SandboxDimensionService, Depends(get_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
    category_code: str | None = Query(None, description="Filter by connector category code"),
) -> list[SandboxDimensionResponse]:
    return await service.list_dimension(dimension_name="connector_types", filter_code=category_code)


@router.get("/signal-statuses", response_model=list[SandboxDimensionResponse])
async def list_signal_statuses(
    service: Annotated[SandboxDimensionService, Depends(get_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[SandboxDimensionResponse]:
    return await service.list_dimension(dimension_name="signal_statuses")


@router.get("/dataset-sources", response_model=list[SandboxDimensionResponse])
async def list_dataset_sources(
    service: Annotated[SandboxDimensionService, Depends(get_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[SandboxDimensionResponse]:
    return await service.list_dimension(dimension_name="dataset_sources")


@router.get("/execution-statuses", response_model=list[SandboxDimensionResponse])
async def list_execution_statuses(
    service: Annotated[SandboxDimensionService, Depends(get_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[SandboxDimensionResponse]:
    return await service.list_dimension(dimension_name="execution_statuses")


@router.get("/dataset-templates", response_model=list[SandboxDimensionResponse])
async def list_dataset_templates(
    service: Annotated[SandboxDimensionService, Depends(get_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
    connector_type_code: str | None = Query(None, description="Filter by connector type code"),
) -> list[SandboxDimensionResponse]:
    return await service.list_dimension(dimension_name="dataset_templates", filter_code=connector_type_code)


@router.get("/threat-severities", response_model=list[SandboxDimensionResponse])
async def list_threat_severities(
    service: Annotated[SandboxDimensionService, Depends(get_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[SandboxDimensionResponse]:
    return await service.list_dimension(dimension_name="threat_severities")


@router.get("/policy-action-types", response_model=list[SandboxDimensionResponse])
async def list_policy_action_types(
    service: Annotated[SandboxDimensionService, Depends(get_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[SandboxDimensionResponse]:
    return await service.list_dimension(dimension_name="policy_action_types")


@router.get("/library-types", response_model=list[SandboxDimensionResponse])
async def list_library_types(
    service: Annotated[SandboxDimensionService, Depends(get_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
) -> list[SandboxDimensionResponse]:
    return await service.list_dimension(dimension_name="library_types")


@router.get("/connector-config-schema", response_model=ConnectorConfigSchemaResponse | None)
async def get_connector_config_schema(
    service: Annotated[SandboxDimensionService, Depends(get_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
    connector_type_code: str = Query(..., description="Connector type code (e.g. github, aws_iam)"),
) -> ConnectorConfigSchemaResponse | None:
    return await service.get_connector_config_schema(connector_type_code=connector_type_code)


@router.get("/asset-versions", response_model=list[AssetVersionResponse])
async def list_asset_versions(
    service: Annotated[SandboxDimensionService, Depends(get_sandbox_dimension_service)],
    claims=Depends(get_current_access_claims),
    connector_type_code: str | None = Query(None, description="Filter by connector type code"),
) -> list[AssetVersionResponse]:
    return await service.list_asset_versions(connector_type_code=connector_type_code)


@router.get("/recommended-libraries", response_model=list[RecommendedLibraryResponse])
async def list_recommended_libraries(
    library_service: Annotated[LibraryService, Depends(get_library_service)],
    claims=Depends(get_current_access_claims),
    connector_type_code: str = Query(..., description="Filter by connector type code"),
    asset_version_id: str | None = Query(None, description="Filter by asset version ID"),
) -> list[RecommendedLibraryResponse]:
    return await library_service.get_recommended_libraries(
        user_id=claims.subject,
        connector_type_code=connector_type_code,
        asset_version_id=asset_version_id,
    )

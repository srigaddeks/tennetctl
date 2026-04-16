from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_dataset_service
from .schemas import (
    AddRecordsRequest,
    AssetSamplesResponse,
    ComposeDatasetRequest,
    ComposeDatasetResponse,
    ConnectorAssetTypesResponse,
    CreateDatasetRequest,
    CreateVersionRequest,
    DatasetDataRecord,
    UpdateRecordDescriptionRequest,
    UpdateRecordNameRequest,
    DatasetListResponse,
    DatasetRecordsResponse,
    DatasetResponse,
    DatasetVersionListResponse,
    FieldOverrideRequest,
    SchemaDriftResponse,
    SmartComposeRequest,
    UpdateDatasetRequest,
    UpdateRecordRequest,
)
from .service import DatasetService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/sb/datasets", tags=["sandbox-datasets"])


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    workspace_id: str | None = Query(default=None),
    connector_instance_id: str | None = Query(default=None),
    dataset_source_code: str | None = Query(default=None),
    is_locked: bool | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> DatasetListResponse:
    return await service.list_datasets(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        connector_instance_id=connector_instance_id,
        dataset_source_code=dataset_source_code,
        is_locked=is_locked,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


@router.get("/asset-types", response_model=ConnectorAssetTypesResponse)
async def get_connector_asset_types(
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    connector_instance_id: str = Query(...),
) -> ConnectorAssetTypesResponse:
    """Discover asset types available for a connector with counts and sample property keys."""
    return await service.get_connector_asset_types(
        user_id=claims.subject,
        org_id=org_id,
        connector_instance_id=connector_instance_id,
    )


@router.get("/asset-samples", response_model=AssetSamplesResponse)
async def get_asset_samples(
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    connector_instance_id: str = Query(...),
    asset_type_code: str = Query(...),
    limit: int = Query(default=5, ge=1, le=50),
) -> AssetSamplesResponse:
    """Preview sample asset records for a connector + asset type combo."""
    return await service.get_asset_samples(
        user_id=claims.subject,
        org_id=org_id,
        connector_instance_id=connector_instance_id,
        asset_type_code=asset_type_code,
        limit=limit,
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
) -> DatasetResponse:
    return await service.get_dataset(
        user_id=claims.subject, dataset_id=dataset_id,
    )


@router.get("/{dataset_id}/records", response_model=DatasetRecordsResponse)
async def get_dataset_records(
    dataset_id: str,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    limit: int = Query(default=500, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
) -> DatasetRecordsResponse:
    return await service.get_dataset_records(
        user_id=claims.subject,
        dataset_id=dataset_id,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    body: CreateDatasetRequest,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> DatasetResponse:
    return await service.create_dataset(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=body,
    )


@router.post("/{dataset_id}/records", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def add_records(
    dataset_id: str,
    body: AddRecordsRequest,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> DatasetResponse:
    return await service.add_records(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        dataset_id=dataset_id,
        request=body,
    )


@router.put("/{dataset_id}/records/{record_id}", response_model=DatasetDataRecord)
async def update_record(
    dataset_id: str,
    record_id: str,
    body: UpdateRecordRequest,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> DatasetDataRecord:
    """Update an individual record's JSON data."""
    return await service.update_record(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        dataset_id=dataset_id,
        record_id=record_id,
        record_data=body.record_data,
    )


@router.delete("/{dataset_id}/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    dataset_id: str,
    record_id: str,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    """Delete an individual record from the dataset."""
    await service.delete_record(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        dataset_id=dataset_id,
        record_id=record_id,
    )


@router.patch("/{dataset_id}/records/{record_id}/name", response_model=DatasetDataRecord)
async def update_record_name(
    dataset_id: str,
    record_id: str,
    body: UpdateRecordNameRequest,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> DatasetDataRecord:
    """Set a unique short name for a record (used in data sufficiency checks)."""
    return await service.update_record_name(
        user_id=claims.subject,
        org_id=org_id,
        dataset_id=dataset_id,
        record_id=record_id,
        record_name=body.record_name,
    )


@router.patch("/{dataset_id}/records/{record_id}/description", response_model=DatasetDataRecord)
async def update_record_description(
    dataset_id: str,
    record_id: str,
    body: UpdateRecordDescriptionRequest,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> DatasetDataRecord:
    """Update the markdown description for an individual record."""
    return await service.update_record_description(
        user_id=claims.subject,
        org_id=org_id,
        dataset_id=dataset_id,
        record_id=record_id,
        description=body.description,
    )


@router.post("/{dataset_id}/generate-descriptions")
async def generate_descriptions(
    dataset_id: str,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
    asset_type: str = Query(default=""),
    connector_type: str = Query(default=""),
) -> dict:
    """Start background AI description generation for all records."""
    return await service.generate_descriptions(
        user_id=claims.subject,
        org_id=org_id,
        dataset_id=dataset_id,
        asset_type=asset_type,
        connector_type=connector_type,
    )


@router.get("/{dataset_id}/generate-descriptions/status")
async def get_generation_status(
    dataset_id: str,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    _claims=Depends(get_current_access_claims),
) -> dict:
    """Get the current status of background description generation."""
    return service.get_generation_status(dataset_id)


@router.get("/{dataset_id}/asset-type-descriptions")
async def get_asset_type_descriptions(
    dataset_id: str,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    _claims=Depends(get_current_access_claims),
) -> dict:
    """Get AI-generated descriptions per asset type for this dataset."""
    return await service.get_asset_type_descriptions(dataset_id)


@router.post("/{dataset_id}/versions", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    dataset_id: str,
    body: CreateVersionRequest,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> DatasetResponse:
    """Snapshot the current dataset as a new immutable version."""
    return await service.create_version(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        dataset_id=dataset_id,
        description=body.description,
    )


@router.get("/{dataset_id}/versions", response_model=DatasetVersionListResponse)
async def list_versions(
    dataset_id: str,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> DatasetVersionListResponse:
    """List all versions of a dataset."""
    return await service.list_versions(
        user_id=claims.subject,
        org_id=org_id,
        dataset_id=dataset_id,
    )


@router.patch("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: str,
    body: UpdateDatasetRequest,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> DatasetResponse:
    return await service.update_dataset(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        dataset_id=dataset_id,
        request=body,
    )


@router.post("/{dataset_id}/lock", response_model=DatasetResponse)
async def lock_dataset(
    dataset_id: str,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> DatasetResponse:
    return await service.lock_dataset(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        dataset_id=dataset_id,
    )


@router.post("/{dataset_id}/clone", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def clone_dataset(
    dataset_id: str,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> DatasetResponse:
    return await service.clone_dataset(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        dataset_id=dataset_id,
    )


@router.patch("/{dataset_id}/fields", response_model=DatasetResponse)
async def update_field_overrides(
    dataset_id: str,
    body: list[FieldOverrideRequest],
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> DatasetResponse:
    return await service.update_field_overrides(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        dataset_id=dataset_id,
        overrides=body,
    )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> None:
    await service.delete_dataset(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        dataset_id=dataset_id,
    )


@router.post("/compose", response_model=ComposeDatasetResponse, status_code=status.HTTP_201_CREATED)
async def compose_dataset(
    body: ComposeDatasetRequest,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> ComposeDatasetResponse:
    """Compose a dataset from collected asset properties grouped by asset type."""
    return await service.compose_dataset(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        request=body,
    )


@router.post("/smart-preview")
async def smart_preview(
    body: SmartComposeRequest,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
):
    """Preview smart-selected samples without creating a dataset."""
    return await service.smart_preview(
        user_id=claims.subject,
        org_id=org_id,
        connector_instance_id=body.connector_instance_id,
        samples_per_type=body.samples_per_type,
    )


@router.post("/smart-compose", response_model=ComposeDatasetResponse, status_code=status.HTTP_201_CREATED)
async def smart_compose_dataset(
    body: SmartComposeRequest,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> ComposeDatasetResponse:
    """Compose a diversity-maximising dataset from all asset types on a connector."""
    return await service.smart_compose_dataset(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        connector_instance_id=body.connector_instance_id,
        name=body.name,
        description=body.description,
        workspace_id=body.workspace_id,
        samples_per_type=body.samples_per_type,
    )


@router.get("/{dataset_id}/schema-drift", response_model=SchemaDriftResponse)
async def check_schema_drift(
    dataset_id: str,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> SchemaDriftResponse:
    """Compare the dataset's stored schema against current asset properties to detect drift."""
    return await service.check_schema_drift(
        user_id=claims.subject,
        dataset_id=dataset_id,
        org_id=org_id,
        tenant_key=claims.tenant_key,
    )

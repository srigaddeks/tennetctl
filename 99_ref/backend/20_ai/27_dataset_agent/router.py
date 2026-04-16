"""
FastAPI routes for the Dataset AI Agent.
Prefix: /api/v1/ai/dataset-agent

Routes:
  POST /explain-record           Explain a single JSON record (fields, compliance relevance)
  POST /explain-dataset          Batch-explain all records in a dataset
  POST /compose-test-data        Generate varied test records from a schema
  POST /enhance-dataset          Analyze dataset quality and suggest improvements
"""
from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends

from .dependencies import get_dataset_agent_service
from .schemas import (
    ComposeTestDataRequest,
    ComposeTestDataResponse,
    EnhanceDatasetRequest,
    EnhanceDatasetResponse,
    ExplainRecordRequest,
    ExplainRecordResponse,
)
from .service import DatasetAgentService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(
    prefix="/api/v1/ai/dataset-agent",
    tags=["ai-dataset-agent"],
)


@router.post("/explain-record", response_model=ExplainRecordResponse)
async def explain_record(
    body: ExplainRecordRequest,
    service: Annotated[DatasetAgentService, Depends(get_dataset_agent_service)],
    claims=Depends(get_current_access_claims),
) -> ExplainRecordResponse:
    """Explain every field in a JSON record — what it means, compliance relevance, signal ideas."""
    result = await service.explain_record(
        user_id=claims.subject,
        record_data=body.record_data,
        asset_type_hint=body.asset_type_hint,
        connector_type=body.connector_type,
    )
    return ExplainRecordResponse(**result)


@router.post("/explain-dataset")
async def explain_dataset(
    body: EnhanceDatasetRequest,
    service: Annotated[DatasetAgentService, Depends(get_dataset_agent_service)],
    claims=Depends(get_current_access_claims),
) -> dict:
    """Batch-explain all records in a dataset with schema-level overview."""
    return await service.explain_dataset_batch(
        user_id=claims.subject,
        records=body.records,
        asset_type=body.asset_type,
        connector_type=body.connector_type,
    )


@router.post("/compose-test-data", response_model=ComposeTestDataResponse)
async def compose_test_data(
    body: ComposeTestDataRequest,
    service: Annotated[DatasetAgentService, Depends(get_dataset_agent_service)],
    claims=Depends(get_current_access_claims),
) -> ComposeTestDataResponse:
    """Generate varied, realistic test records from a schema (compliant, non-compliant, edge cases)."""
    result = await service.compose_test_data(
        user_id=claims.subject,
        property_keys=body.property_keys,
        sample_records=body.sample_records,
        asset_type=body.asset_type,
        connector_type=body.connector_type,
        record_count=body.record_count,
    )
    return ComposeTestDataResponse(**result)


@router.post("/enhance-dataset", response_model=EnhanceDatasetResponse)
async def enhance_dataset(
    body: EnhanceDatasetRequest,
    service: Annotated[DatasetAgentService, Depends(get_dataset_agent_service)],
    claims=Depends(get_current_access_claims),
) -> EnhanceDatasetResponse:
    """Analyze dataset quality — find gaps, missing scenarios, suggest improvements."""
    result = await service.enhance_dataset(
        user_id=claims.subject,
        records=body.records,
        asset_type=body.asset_type,
        connector_type=body.connector_type,
    )
    return EnhanceDatasetResponse(**result)

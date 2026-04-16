"""Pydantic schemas for Dataset AI Agent."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ExplainRecordRequest(BaseModel):
    record_data: dict = Field(..., description="The JSON record to explain")
    asset_type_hint: str | None = Field(None, description="Optional hint about the asset type")
    connector_type: str | None = Field(None, description="e.g. github, azure, postgres")


class FieldExplanation(BaseModel):
    field_name: str
    data_type: str
    description: str
    compliance_relevance: str  # high | medium | low | none
    example_signal_uses: list[str] = Field(default_factory=list)
    anomaly_indicators: list[str] = Field(default_factory=list)


class RecommendedSignal(BaseModel):
    signal_name: str
    description: str
    fields_used: list[str] = Field(default_factory=list)
    expected_result: str = ""


class ExplainRecordResponse(BaseModel):
    asset_type: str
    record_summary: str
    total_fields: int
    fields: list[FieldExplanation]
    recommended_signals: list[RecommendedSignal] = Field(default_factory=list)


class ComposeTestDataRequest(BaseModel):
    """Request to generate varied test records from a schema."""
    property_keys: list[str] = Field(..., min_length=1, description="Field names from the asset type")
    sample_records: list[dict] = Field(default_factory=list, description="1-3 sample records for context")
    asset_type: str = Field(..., description="e.g. github_repo")
    connector_type: str | None = Field(None, description="e.g. github")
    record_count: int = Field(default=10, ge=3, le=30)


class GeneratedRecord(BaseModel):
    scenario_name: str = Field(alias="_scenario_name", default="")
    expected_result: str = Field(alias="_expected_result", default="pass")
    explanation: str = Field(alias="_explanation", default="")
    record_data: dict = Field(default_factory=dict)


class ComposeTestDataResponse(BaseModel):
    asset_type: str
    schema_summary: str
    generated_records: list[dict]  # raw dicts including _scenario_name etc.
    coverage_notes: str = ""


class EnhanceDatasetRequest(BaseModel):
    """Request to analyze and suggest improvements for a dataset."""
    records: list[dict] = Field(..., min_length=1, max_length=100)
    asset_type: str = ""
    connector_type: str | None = None


class DatasetGap(BaseModel):
    gap: str
    severity: str  # critical | high | medium | low
    suggestion: str


class MissingScenario(BaseModel):
    scenario_name: str
    description: str
    expected_result: str
    example_record: dict = Field(default_factory=dict)


class FieldCoverage(BaseModel):
    unique_values_seen: int
    coverage: str  # good | fair | poor
    suggestion: str = ""


class EnhanceDatasetResponse(BaseModel):
    quality_score: int = 0
    strengths: list[str] = Field(default_factory=list)
    gaps: list[DatasetGap] = Field(default_factory=list)
    missing_scenarios: list[MissingScenario] = Field(default_factory=list)
    field_coverage: dict[str, FieldCoverage] = Field(default_factory=dict)

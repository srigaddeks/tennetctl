from __future__ import annotations

from pydantic import BaseModel, Field


class CreateThreatTypeRequest(BaseModel):
    threat_code: str = Field(
        ..., min_length=2, max_length=100, pattern=r"^[a-z0-9_]{2,100}$"
    )
    workspace_id: str | None = None
    severity_code: str = Field(default="medium", min_length=1, max_length=50)
    expression_tree: dict = Field(...)
    properties: dict[str, str] | None = None


class UpdateThreatTypeRequest(BaseModel):
    severity_code: str | None = Field(None, min_length=1, max_length=50)
    expression_tree: dict | None = None
    properties: dict[str, str] | None = None


class SimulateThreatRequest(BaseModel):
    signal_results: dict[str, str] = Field(
        ..., description="Signal results to simulate, e.g. {'mfa_disabled': 'fail', 'unusual_login': 'pass'}"
    )


class EvaluationTraceEntry(BaseModel):
    node_type: str
    signal_code: str | None = None
    expected_result: str | None = None
    actual_result: str | None = None
    operator: str | None = None
    result: bool


class SimulateThreatResponse(BaseModel):
    is_triggered: bool
    evaluation_trace: list[EvaluationTraceEntry]


class ThreatTypeResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None = None
    threat_code: str
    version_number: int
    severity_code: str
    severity_name: str | None = None
    expression_tree: dict | None = None
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None = None
    description: str | None = None
    properties: dict[str, str] | None = None


class ThreatTypeListResponse(BaseModel):
    items: list[ThreatTypeResponse]
    total: int

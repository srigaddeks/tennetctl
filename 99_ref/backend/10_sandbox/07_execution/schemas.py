from __future__ import annotations

from pydantic import BaseModel, Field


class ExecuteSignalRequest(BaseModel):
    signal_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)


class BatchExecuteRequest(BaseModel):
    signal_ids: list[str] = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)


class RunResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    signal_id: str
    signal_code: str | None = None
    dataset_id: str | None = None
    live_session_id: str | None = None
    execution_status_code: str
    execution_status_name: str | None = None
    result_code: str | None = None
    result_summary: str | None = None
    result_details: list[dict] | None = None
    execution_time_ms: int | None = None
    error_message: str | None = None
    stdout_capture: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str
    signal_name: str | None = None


class RunListResponse(BaseModel):
    items: list[RunResponse]
    total: int


class ThreatEvaluationResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    threat_type_id: str
    is_triggered: bool
    signal_results: dict
    expression_snapshot: dict
    evaluation_trace: list[dict] | None = None
    live_session_id: str | None = None
    evaluated_at: str
    created_by: str | None = None


class ThreatEvaluationListResponse(BaseModel):
    items: list[ThreatEvaluationResponse]
    total: int


class PolicyExecutionResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    policy_id: str
    threat_evaluation_id: str
    actions_executed: list[dict]
    actions_failed: list[dict] | None = None
    executed_at: str
    created_by: str | None = None


class PolicyExecutionListResponse(BaseModel):
    items: list[PolicyExecutionResponse]
    total: int


class BatchExecuteResponse(BaseModel):
    signal_results: dict[str, RunResponse]
    threat_evaluations: list[ThreatEvaluationResponse]
    policy_executions: list[PolicyExecutionResponse]

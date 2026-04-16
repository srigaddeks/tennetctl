from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExecutionResult:
    """Immutable result from a sandboxed signal execution."""
    status: str                              # completed, failed, timeout
    result_code: str | None = None           # pass, fail, warning
    result_summary: str = ""
    result_details: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    stdout_capture: str = ""
    error_message: str | None = None
    execution_time_ms: int = 0


@dataclass(frozen=True)
class SandboxRunRecord:
    """PG row from 65_vw_run_detail."""
    id: str
    tenant_key: str
    org_id: str
    signal_id: str
    signal_code: str
    dataset_id: str | None
    live_session_id: str | None
    execution_status_code: str
    execution_status_name: str | None
    result_code: str | None
    result_summary: str | None
    execution_time_ms: int | None
    started_at: str | None
    completed_at: str | None
    created_at: str
    signal_name: str | None
    result_details: list | dict | None = None


@dataclass(frozen=True)
class SandboxRunDetailRecord:
    """Full PG row from 25_trx_sandbox_runs — includes JSONB / TEXT columns."""
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None
    signal_id: str
    signal_code: str | None
    dataset_id: str | None
    live_session_id: str | None
    execution_status_code: str
    execution_status_name: str | None
    result_code: str | None
    result_summary: str | None
    result_details: list[dict] | None
    execution_time_ms: int | None
    error_message: str | None
    stdout_capture: str | None
    started_at: str | None
    completed_at: str | None
    created_at: str
    signal_name: str | None


@dataclass(frozen=True)
class ThreatEvaluationRecord:
    """PG row from 26_trx_threat_evaluations."""
    id: str
    tenant_key: str
    org_id: str
    threat_type_id: str
    is_triggered: bool
    signal_results: dict
    expression_snapshot: dict
    live_session_id: str | None
    evaluated_at: str
    created_by: str | None


@dataclass(frozen=True)
class PolicyExecutionRecord:
    """PG row from 27_trx_policy_executions."""
    id: str
    tenant_key: str
    org_id: str
    policy_id: str
    threat_evaluation_id: str
    actions_executed: list[dict]
    actions_failed: list[dict] | None
    executed_at: str
    created_by: str | None

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SignalRecord:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None
    signal_code: str
    version_number: int
    signal_status_code: str
    signal_status_name: str | None
    python_hash: str | None
    timeout_ms: int
    max_memory_mb: int
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None
    description: str | None
    python_source: str | None
    source_prompt: str | None
    caep_event_type: str | None
    risc_event_type: str | None


@dataclass(frozen=True)
class SignalTestExpectationRecord:
    id: str
    signal_id: str
    dataset_id: str
    expected_result_code: str
    expected_summary_pattern: str | None

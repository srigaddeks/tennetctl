from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TestExecutionRecord:
    id: str
    control_test_id: str
    control_id: str | None
    tenant_key: str
    result_status: str
    execution_type: str
    executed_by: str | None
    executed_at: str
    notes: str | None
    evidence_summary: str | None
    score: int | None
    is_active: bool
    created_at: str
    updated_at: str
    test_code: str | None = None
    test_name: str | None = None

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TreatmentPlanRecord:
    id: str
    risk_id: str
    tenant_key: str
    plan_status: str
    target_date: str | None
    completed_at: str | None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None

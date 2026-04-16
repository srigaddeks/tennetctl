from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskRecord:
    id: str
    tenant_key: str
    risk_code: str
    org_id: str
    workspace_id: str
    risk_category_code: str
    risk_level_code: str
    treatment_type_code: str
    source_type: str
    risk_status: str
    is_active: bool
    version: int
    created_at: str
    updated_at: str
    created_by: str | None


@dataclass(frozen=True)
class RiskDetailRecord:
    id: str
    tenant_key: str
    risk_code: str
    org_id: str
    workspace_id: str
    risk_category_code: str
    category_name: str | None
    risk_level_code: str
    risk_level_name: str | None
    risk_level_color: str | None
    treatment_type_code: str
    treatment_type_name: str | None
    source_type: str
    risk_status: str
    is_active: bool
    version: int
    created_at: str
    updated_at: str
    created_by: str | None
    title: str | None
    description: str | None
    notes: str | None
    owner_user_id: str | None
    business_impact: str | None
    inherent_risk_score: int | None
    residual_risk_score: int | None
    linked_control_count: int
    treatment_plan_status: str | None
    treatment_plan_target_date: str | None

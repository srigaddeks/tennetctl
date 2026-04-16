from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GlobalRiskRecord:
    id: str
    tenant_key: str
    risk_code: str
    risk_category_code: str
    risk_level_code: str | None
    inherent_likelihood: int | None
    inherent_impact: int | None
    inherent_risk_score: int | None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None


@dataclass(frozen=True)
class GlobalRiskDetailRecord:
    id: str
    tenant_key: str
    risk_code: str
    risk_category_code: str
    risk_category_name: str | None
    risk_level_code: str | None
    risk_level_name: str | None
    risk_level_color: str | None
    inherent_likelihood: int | None
    inherent_impact: int | None
    inherent_risk_score: int | None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None
    title: str | None
    description: str | None
    short_description: str | None
    mitigation_guidance: str | None
    detection_guidance: str | None
    linked_control_count: int

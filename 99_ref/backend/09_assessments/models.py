from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AssessmentRecord:
    id: str
    tenant_key: str
    assessment_code: str
    org_id: str
    workspace_id: str | None
    framework_id: str | None
    assessment_type_code: str
    assessment_status_code: str
    lead_assessor_id: str | None
    scheduled_start: str | None
    scheduled_end: str | None
    actual_start: str | None
    actual_end: str | None
    is_locked: bool
    assessment_type_name: str | None
    assessment_status_name: str | None
    name: str | None
    description: str | None
    scope_notes: str | None
    finding_count: int
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None


@dataclass(frozen=True)
class FindingRecord:
    id: str
    assessment_id: str
    control_id: str | None
    risk_id: str | None
    severity_code: str
    finding_type: str
    finding_status_code: str
    assigned_to: str | None
    remediation_due_date: str | None
    severity_name: str | None
    finding_status_name: str | None
    title: str | None
    description: str | None
    recommendation: str | None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None


@dataclass(frozen=True)
class FindingResponseRecord:
    id: str
    finding_id: str
    responder_id: str
    response_text: str | None
    responded_at: str
    created_at: str


@dataclass(frozen=True)
class AssessmentTypeRecord:
    id: str
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool


@dataclass(frozen=True)
class FindingSeverityRecord:
    id: str
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool


@dataclass(frozen=True)
class FindingStatusRecord:
    id: str
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControlMappingRecord:
    id: str
    risk_id: str
    control_id: str
    link_type: str
    notes: str | None
    created_at: str
    created_by: str | None
    # Approval workflow
    approval_status: str = "approved"   # pending | approved | rejected
    approved_by: str | None = None
    approved_at: str | None = None
    rejection_reason: str | None = None
    ai_confidence: float | None = None
    ai_rationale: str | None = None
    # Derived joins
    control_code: str | None = None
    control_name: str | None = None
    approved_by_name: str | None = None
    # Risk join (used in pending-mappings list across risks)
    risk_code: str | None = None
    risk_title: str | None = None

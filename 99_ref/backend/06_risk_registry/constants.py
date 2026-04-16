from __future__ import annotations

from enum import StrEnum


class RiskAuditEventType(StrEnum):
    RISK_CREATED = "risk_created"
    RISK_UPDATED = "risk_updated"
    RISK_DELETED = "risk_deleted"
    RISK_ASSESSED = "risk_assessed"
    TREATMENT_PLAN_CREATED = "treatment_plan_created"
    TREATMENT_PLAN_UPDATED = "treatment_plan_updated"
    CONTROL_LINKED = "control_linked"
    CONTROL_UNLINKED = "control_unlinked"
    REVIEW_EVENT_CREATED = "review_event_created"
    GROUP_ASSIGNED = "risk_group_assigned"
    GROUP_UNASSIGNED = "risk_group_unassigned"
    APPETITE_UPDATED = "risk_appetite_updated"
    REVIEW_SCHEDULED = "risk_review_scheduled"
    REVIEW_COMPLETED = "risk_review_completed"


# Valid status transitions — enforcement prevents invalid moves
RISK_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "identified": {"assessed", "closed"},
    "assessed": {"treating", "accepted", "closed"},
    "treating": {"assessed", "accepted", "closed"},
    "accepted": {"treating", "closed"},  # can reopen
    "closed": set(),  # terminal
}

TERMINAL_RISK_STATUSES = frozenset({"closed"})

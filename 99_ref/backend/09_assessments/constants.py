from __future__ import annotations

from enum import StrEnum


class AssessmentAuditEventType(StrEnum):
    ASSESSMENT_CREATED = "assessment_created"
    ASSESSMENT_UPDATED = "assessment_updated"
    ASSESSMENT_COMPLETED = "assessment_completed"
    ASSESSMENT_CANCELLED = "assessment_cancelled"
    ASSESSMENT_DELETED = "assessment_deleted"
    FINDING_CREATED = "finding_created"
    FINDING_UPDATED = "finding_updated"
    FINDING_STATUS_CHANGED = "finding_status_changed"
    FINDING_DELETED = "finding_deleted"
    FINDING_RESPONSE_SUBMITTED = "finding_response_submitted"


ASSESSMENT_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "planned":     {"in_progress", "cancelled"},
    "in_progress": {"review", "completed", "cancelled"},
    "review":      {"in_progress", "completed", "cancelled"},
    "completed":   set(),   # terminal
    "cancelled":   set(),   # terminal
}

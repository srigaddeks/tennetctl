from __future__ import annotations
from enum import StrEnum


class FeedbackAuditEventType(StrEnum):
    TICKET_CREATED = "ticket_created"
    TICKET_UPDATED = "ticket_updated"
    TICKET_DELETED = "ticket_deleted"
    STATUS_CHANGED = "status_changed"
    PRIORITY_CHANGED = "priority_changed"
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_UNASSIGNED = "ticket_unassigned"


# Valid status transitions: current_status -> set of allowed next statuses
VALID_TRANSITIONS: dict[str, frozenset[str]] = {
    "open":        frozenset({"in_review", "in_progress", "resolved", "closed", "wont_fix", "duplicate"}),
    "in_review":   frozenset({"open", "in_progress", "resolved", "closed", "wont_fix", "duplicate"}),
    "in_progress": frozenset({"in_review", "resolved", "closed", "wont_fix", "duplicate"}),
    "resolved":    frozenset({"open", "closed"}),
    "closed":      frozenset({"open"}),
    "wont_fix":    frozenset({"open"}),
    "duplicate":   frozenset({"open"}),
}

TERMINAL_STATUSES: frozenset[str] = frozenset({"resolved", "closed", "wont_fix", "duplicate"})

# These property keys are only visible to users with feedback.manage permission
INTERNAL_PROPERTY_KEYS: frozenset[str] = frozenset({"admin_note"})

# EAV property keys that are user-settable
USER_PROPERTY_KEYS: frozenset[str] = frozenset({
    "title", "description", "context_url", "browser_info",
    "steps_to_reproduce", "expected_behavior", "actual_behavior", "version_info",
})

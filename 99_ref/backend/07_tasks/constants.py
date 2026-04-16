from __future__ import annotations

from enum import StrEnum


class TaskAuditEventType(StrEnum):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_REASSIGNED = "task_reassigned"
    TASK_PRIORITY_CHANGED = "task_priority_changed"
    TASK_DUE_DATE_CHANGED = "task_due_date_changed"
    TASK_COMMENT_ADDED = "task_comment_added"
    TASK_ASSIGNMENT_ADDED = "task_assignment_added"
    TASK_ASSIGNMENT_REMOVED = "task_assignment_removed"
    TASK_DEPENDENCY_ADDED = "task_dependency_added"
    TASK_DEPENDENCY_REMOVED = "task_dependency_removed"
    TASK_START_DATE_CHANGED = "task_start_date_changed"


# Allowed status transitions — enforce in service layer.
# Evidence approval chain: open → in_progress → pending_verification → in_review
#   → published → resolved
# in_review and published can be rejected back to in_progress.
TASK_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "open":                 ["in_progress", "cancelled"],
    "in_progress":          ["pending_verification", "open", "cancelled"],
    "pending_verification": ["in_review", "in_progress"],   # submitted → under review or rejected back
    "in_review":            ["published", "in_progress"],   # approved → published or rejected back
    "published":            ["resolved"],                   # auditor marks complete
    "resolved":             [],
    "cancelled":            [],
    "overdue":              ["in_progress", "cancelled"],
}

# Permission code required for specific status transitions.
# Transitions not listed here are allowed for any user who can tasks.update.
TASK_TRANSITION_PERMISSION: dict[tuple[str, str], str] = {
    ("in_progress",          "pending_verification"): "tasks.submit",
    ("pending_verification", "in_review"):            "tasks.review",
    ("in_review",            "in_progress"):          "tasks.review",    # reject back
    ("in_review",            "published"):            "tasks.approve",
    ("published",            "resolved"):             "tasks.complete",
}

# Finding status transitions — enforce in service layer.
FINDING_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "open":            ["acknowledged"],
    "acknowledged":    ["in_remediation", "disputed"],
    "in_remediation":  ["responded"],
    "disputed":        ["responded"],
    "responded":       ["auditor_review"],
    "auditor_review":  ["verified_closed", "accepted", "escalated"],
    "verified_closed": [],
    "accepted":        [],
    "escalated":       ["auditor_review"],
}

# Permission code required for specific finding transitions.
FINDING_TRANSITION_PERMISSION: dict[tuple[str, str], str] = {
    ("open",           "acknowledged"):    "findings.respond",
    ("acknowledged",   "in_remediation"): "findings.respond",
    ("acknowledged",   "disputed"):       "findings.respond",
    ("in_remediation", "responded"):      "findings.respond",
    ("disputed",       "responded"):      "findings.respond",
    ("responded",      "auditor_review"): "findings.respond",
    ("auditor_review", "verified_closed"): "findings.close",
    ("auditor_review", "accepted"):       "findings.close",
    ("auditor_review", "escalated"):      "findings.close",
    ("escalated",      "auditor_review"): "findings.close",
}

# Allowlist for sort_by query param (guards against SQL injection)
VALID_SORT_FIELDS = frozenset({"due_date", "priority", "created_at", "updated_at"})

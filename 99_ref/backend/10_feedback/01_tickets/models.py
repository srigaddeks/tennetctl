from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class TicketRecord:
    id: str
    tenant_key: str
    submitted_by: str
    ticket_type_code: str
    status_code: str
    priority_code: str
    org_id: str | None
    workspace_id: str | None
    is_deleted: bool
    created_at: str
    updated_at: str
    resolved_at: str | None
    resolved_by: str | None


@dataclass(frozen=True)
class TicketDetailRecord:
    id: str
    tenant_key: str
    submitted_by: str
    ticket_type_code: str
    status_code: str
    priority_code: str
    org_id: str | None
    workspace_id: str | None
    is_deleted: bool
    created_at: str
    updated_at: str
    resolved_at: str | None
    resolved_by: str | None
    # From EAV properties
    title: str | None
    description: str | None
    context_url: str | None
    browser_info: str | None
    steps_to_reproduce: str | None
    expected_behavior: str | None
    actual_behavior: str | None
    version_info: str | None
    admin_note: str | None  # internal only
    # From auth schema join
    submitter_email: str | None
    submitter_display_name: str | None
    # Assignments
    active_assignments: list[dict]


@dataclass(frozen=True)
class TicketEventRecord:
    id: str
    ticket_id: str
    tenant_key: str
    event_type: str
    actor_id: str
    occurred_at: str
    old_value: str | None
    new_value: str | None
    note: str | None


@dataclass(frozen=True)
class TicketTypeDimRecord:
    code: str
    name: str
    description: str | None
    icon_name: str | None
    sort_order: int
    is_active: bool


@dataclass(frozen=True)
class TicketStatusDimRecord:
    code: str
    name: str
    description: str | None
    is_terminal: bool
    sort_order: int


@dataclass(frozen=True)
class TicketPriorityDimRecord:
    code: str
    name: str
    description: str | None
    numeric_level: int
    sort_order: int

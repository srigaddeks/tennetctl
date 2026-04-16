from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskRecord:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str
    task_type_code: str
    priority_code: str
    status_code: str
    entity_type: str | None
    entity_id: str | None
    assignee_user_id: str | None
    reporter_user_id: str
    due_date: str | None
    start_date: str | None
    completed_at: str | None
    estimated_hours: float | None
    actual_hours: float | None
    is_active: bool
    version: int
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class TaskDetailRecord:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str
    task_type_code: str
    task_type_name: str
    priority_code: str
    priority_name: str
    status_code: str
    status_name: str
    is_terminal: bool
    entity_type: str | None
    entity_id: str | None
    assignee_user_id: str | None
    reporter_user_id: str
    due_date: str | None
    start_date: str | None
    completed_at: str | None
    estimated_hours: float | None
    actual_hours: float | None
    is_active: bool
    version: int
    created_at: str
    updated_at: str
    title: str | None
    description: str | None
    acceptance_criteria: str | None
    resolution_notes: str | None
    remediation_plan: str | None
    co_assignee_count: int
    blocker_count: int
    comment_count: int

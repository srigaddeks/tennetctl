from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CreateTaskRequest(BaseModel):
    org_id: str
    workspace_id: str
    task_type_code: str = Field(..., min_length=1, max_length=50)
    priority_code: str = Field(default="medium", max_length=50)
    entity_type: str | None = Field(None, max_length=50)
    entity_id: str | None = None
    assignee_user_id: str | None = None
    due_date: str | None = None
    start_date: str | None = None

    @field_validator("entity_type", "entity_id", "assignee_user_id", "due_date", "start_date", mode="before")
    @classmethod
    def _empty_string_to_none(cls, v):
        if isinstance(v, str) and v == "":
            return None
        return v
    estimated_hours: float | None = Field(None, ge=0)
    # EAV properties
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    acceptance_criteria: str | None = None
    remediation_plan: str | None = None

    @field_validator("entity_type", "entity_id", "assignee_user_id", mode="before")
    @classmethod
    def _normalize_optional_blank_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class UpdateTaskRequest(BaseModel):
    priority_code: str | None = Field(None, max_length=50)
    status_code: str | None = Field(None, max_length=50)
    assignee_user_id: str | None = None
    due_date: str | None = None
    start_date: str | None = None
    estimated_hours: float | None = Field(None, ge=0)
    actual_hours: float | None = Field(None, ge=0)
    # EAV properties
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    acceptance_criteria: str | None = None
    resolution_notes: str | None = None
    remediation_plan: str | None = None


class TaskDetailResponse(BaseModel):
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
    entity_type: str | None = None
    entity_id: str | None = None
    assignee_user_id: str | None = None
    reporter_user_id: str
    due_date: str | None = None
    start_date: str | None = None
    completed_at: str | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None
    is_active: bool
    version: int = 1
    created_at: str
    updated_at: str
    title: str | None = None
    description: str | None = None
    acceptance_criteria: str | None = None
    resolution_notes: str | None = None
    remediation_plan: str | None = None
    co_assignee_count: int = 0
    blocker_count: int = 0
    comment_count: int = 0
    entity_name: str | None = None


class TaskListResponse(BaseModel):
    items: list[TaskDetailResponse]
    total: int


class BulkUpdateTaskRequest(BaseModel):
    task_ids: list[str] = Field(..., min_length=1, max_length=100)
    status_code: str | None = Field(None, max_length=50)
    priority_code: str | None = Field(None, max_length=50)
    assignee_user_id: str | None = None


class BulkUpdateTaskResponse(BaseModel):
    updated_count: int
    failed_ids: list[str] = []


class TaskTypeSummary(BaseModel):
    task_type_code: str
    task_type_name: str
    count: int


class TaskSummaryResponse(BaseModel):
    open_count: int = 0
    in_progress_count: int = 0
    pending_verification_count: int = 0
    resolved_count: int = 0
    cancelled_count: int = 0
    overdue_count: int = 0
    resolved_this_week_count: int = 0
    by_type: list[TaskTypeSummary] = []


class ImportTaskError(BaseModel):
    row: int
    key: str | None = None
    field: str | None = None
    message: str


class ImportTasksResult(BaseModel):
    created: int
    updated: int
    skipped: int = 0
    warnings: list[str] = []
    errors: list[ImportTaskError] = []
    dry_run: bool = False

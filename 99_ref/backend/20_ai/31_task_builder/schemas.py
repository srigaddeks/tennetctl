"""Pydantic schemas for the AI task builder module."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


TaskTypeCode = Literal["evidence_collection", "control_remediation"]
PriorityCode = Literal["critical", "high", "medium", "low"]


# ── Generated task / group ────────────────────────────────────────────────────


class GeneratedTask(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    priority_code: PriorityCode = "medium"
    due_days_from_now: int = Field(default=30, ge=1, le=365)
    acceptance_criteria: str = Field(..., min_length=1)
    task_type_code: TaskTypeCode
    remediation_plan: str | None = None


class TaskGroupResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    control_id: str
    control_code: str
    tasks: list[GeneratedTask] = Field(default_factory=list)


# ── Legacy direct endpoints (kept for backwards compat) ──────────────────────


class PreviewRequest(BaseModel):
    framework_id: str
    org_id: str | None = None
    workspace_id: str | None = None
    user_context: str = ""
    control_ids: list[str] | None = None
    attachment_ids: list[str] | None = None


class ApplyRequest(BaseModel):
    framework_id: str
    org_id: str
    workspace_id: str
    task_groups: list[TaskGroupResponse]


class ApplyResponse(BaseModel):
    created: int = 0
    skipped: int = 0


# ── Session ───────────────────────────────────────────────────────────────────


class CreateTaskBuilderSessionRequest(BaseModel):
    framework_id: str
    scope_org_id: str
    scope_workspace_id: str
    user_context: str = ""
    attachment_ids: list[str] = Field(default_factory=list)
    control_ids: list[str] | None = None


class PatchTaskBuilderSessionRequest(BaseModel):
    user_context: str | None = None
    attachment_ids: list[str] | None = None
    control_ids: list[str] | None = None
    proposed_tasks: list[dict[str, Any]] | None = None


class TaskBuilderSessionResponse(BaseModel):
    id: str
    tenant_key: str
    user_id: str
    status: str
    framework_id: str
    scope_org_id: str | None
    scope_workspace_id: str | None
    user_context: str
    attachment_ids: list[str]
    control_ids: list[str] | None
    proposed_tasks: list[dict[str, Any]] | None
    apply_result: dict[str, Any] | None
    job_id: str | None
    error_message: str | None
    activity_log: list[dict] = Field(default_factory=list)
    created_at: str
    updated_at: str


class TaskBuilderSessionListResponse(BaseModel):
    items: list[TaskBuilderSessionResponse]
    total: int


# ── Job status ────────────────────────────────────────────────────────────────


class TaskBuilderJobStatusResponse(BaseModel):
    job_id: str
    status: str          # queued | running | completed | failed
    job_type: str
    creation_log: list[dict] = Field(default_factory=list)
    stats: dict | None = None
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None

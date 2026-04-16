from __future__ import annotations

from pydantic import BaseModel, Field


class CreateTreatmentPlanRequest(BaseModel):
    plan_status: str = Field(default="draft", pattern=r"^(draft|active|completed|cancelled)$")
    target_date: str | None = None
    # EAV properties
    plan_description: str | None = None
    action_items: str | None = None
    compensating_control_description: str | None = None
    approver_user_id: str | None = None
    approval_notes: str | None = None
    review_frequency: str | None = None
    properties: dict[str, str] | None = None


class UpdateTreatmentPlanRequest(BaseModel):
    plan_status: str | None = Field(None, pattern=r"^(draft|active|completed|cancelled)$")
    target_date: str | None = None
    # EAV properties
    plan_description: str | None = None
    action_items: str | None = None
    compensating_control_description: str | None = None
    approver_user_id: str | None = None
    approval_notes: str | None = None
    review_frequency: str | None = None
    properties: dict[str, str] | None = None


class TreatmentPlanResponse(BaseModel):
    id: str
    risk_id: str
    tenant_key: str
    plan_status: str
    target_date: str | None = None
    completed_at: str | None = None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None = None
    properties: dict[str, str] | None = None

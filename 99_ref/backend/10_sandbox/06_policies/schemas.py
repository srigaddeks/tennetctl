from __future__ import annotations

from pydantic import BaseModel, Field


class CreatePolicyRequest(BaseModel):
    policy_code: str = Field(
        ..., min_length=2, max_length=100, pattern=r"^[a-z0-9_]{2,100}$"
    )
    workspace_id: str | None = None
    threat_type_id: str = Field(..., min_length=1)
    actions: list[dict] = Field(
        ...,
        min_length=1,
        description="List of action dicts, each with action_type + config",
    )
    is_enabled: bool = True
    cooldown_minutes: int = Field(default=0, ge=0)
    properties: dict[str, str] | None = None


class UpdatePolicyRequest(BaseModel):
    threat_type_id: str | None = None
    actions: list[dict] | None = None
    cooldown_minutes: int | None = Field(default=None, ge=0)
    properties: dict[str, str] | None = None


class PolicyResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None = None
    policy_code: str
    version_number: int
    threat_type_id: str
    threat_code: str | None = None
    actions: list[dict]
    is_enabled: bool
    cooldown_minutes: int
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None = None
    description: str | None = None
    properties: dict[str, str] | None = None


class PolicyListResponse(BaseModel):
    items: list[PolicyResponse]
    total: int


class PolicyTestResponse(BaseModel):
    actions_simulated: list[dict]
    would_fire: bool


class PolicyExecutionResponse(BaseModel):
    id: str
    policy_id: str
    threat_evaluation_id: str | None = None
    actions_executed: list[dict]
    actions_failed: list[dict]
    executed_at: str

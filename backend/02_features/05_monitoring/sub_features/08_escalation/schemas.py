"""Pydantic schemas for monitoring.escalation (40-01)."""

from __future__ import annotations

import json as _json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


PriorityLevel = Literal[1, 2, 3, 4]  # 1=low, 2=normal, 3=high, 4=critical
StepKind = Literal["notify_user", "notify_group", "notify_oncall", "wait", "repeat"]
RotationKind = Literal[1]  # 1=simple_round_robin (extensible)


class EscalationStep(BaseModel):
    """Single step in an escalation policy."""
    model_config = ConfigDict(extra="forbid")

    kind: StepKind
    target_ref: dict[str, Any] | None = None  # {user_id?|group_id?|schedule_id?}
    wait_seconds: int | None = Field(default=None, ge=0, le=86400)
    priority: PriorityLevel = Field(default=2)


class EscalationPolicyCreateRequest(BaseModel):
    """Create escalation policy."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    steps: list[EscalationStep] = Field(min_length=1)


class EscalationPolicyUpdateRequest(BaseModel):
    """Update escalation policy (replaces step set entirely)."""
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None
    steps: list[EscalationStep] | None = Field(default=None, min_length=1)


class EscalationPolicyStepResponse(BaseModel):
    """Single step in response."""
    model_config = ConfigDict(extra="ignore")

    step_order: int
    kind_id: int
    kind_code: str
    kind_label: str
    target_ref: dict[str, Any]
    wait_seconds: int | None
    priority: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EscalationPolicyStepResponse":
        return cls(**data)


class EscalationPolicyResponse(BaseModel):
    """Escalation policy response."""
    model_config = ConfigDict(extra="ignore")

    id: str
    org_id: str
    name: str
    description: str | None
    is_active: bool
    steps: list[EscalationPolicyStepResponse]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "EscalationPolicyResponse":
        steps_raw = row.get("steps") or []
        steps = [EscalationPolicyStepResponse.from_dict(s) for s in steps_raw] if steps_raw else []
        return cls(
            id=str(row["id"]),
            org_id=str(row["org_id"]),
            name=row["name"],
            description=row.get("description"),
            is_active=row.get("is_active", True),
            steps=steps,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class OncallMember(BaseModel):
    """On-call schedule member."""
    model_config = ConfigDict(extra="forbid")

    member_order: int
    user_id: str


class OncallScheduleCreateRequest(BaseModel):
    """Create on-call schedule."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    timezone: str = Field(default="UTC")
    rotation_period_seconds: int = Field(ge=60, le=31536000)  # 1 min to 1 year
    rotation_start: datetime
    members: list[str] = Field(min_length=1)  # List of user IDs in order


class OncallScheduleUpdateRequest(BaseModel):
    """Update on-call schedule (replaces members entirely)."""
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    timezone: str | None = None
    rotation_period_seconds: int | None = Field(default=None, ge=60, le=31536000)
    rotation_start: datetime | None = None
    members: list[str] | None = None


class OncallScheduleMemberResponse(BaseModel):
    """On-call schedule member in response."""
    model_config = ConfigDict(extra="ignore")

    member_order: int
    user_id: str
    user_email: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OncallScheduleMemberResponse":
        return cls(**data)


class OncallScheduleResponse(BaseModel):
    """On-call schedule response."""
    model_config = ConfigDict(extra="ignore")

    id: str
    org_id: str
    name: str
    description: str | None
    timezone: str
    rotation_period_seconds: int
    rotation_start: datetime
    members: list[OncallScheduleMemberResponse]
    current_oncall_user_id: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "OncallScheduleResponse":
        members_raw = row.get("members") or []
        members = [OncallScheduleMemberResponse.from_dict(m) for m in members_raw] if members_raw else []
        return cls(
            id=str(row["id"]),
            org_id=str(row["org_id"]),
            name=row["name"],
            description=row.get("description"),
            timezone=row["timezone"],
            rotation_period_seconds=row["rotation_period_seconds"],
            rotation_start=row["rotation_start"],
            members=members,
            current_oncall_user_id=row.get("current_oncall_user_id"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class OncallWhoamiResponse(BaseModel):
    """Response for /whoami endpoint."""
    model_config = ConfigDict(extra="forbid")

    user_id: str
    user_email: str
    on_until: datetime
    schedule_id: str
    schedule_name: str


class AlertAckRequest(BaseModel):
    """Acknowledge an alert."""
    model_config = ConfigDict(extra="forbid")

    note: str | None = Field(default=None, max_length=1000)

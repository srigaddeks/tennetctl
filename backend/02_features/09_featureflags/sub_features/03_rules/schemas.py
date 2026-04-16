"""featureflags.rules — Pydantic v2 API models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

FlagEnvironment = Literal["dev", "staging", "prod", "test"]


class RuleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    flag_id: str
    environment: FlagEnvironment
    priority: int = Field(ge=0, le=32000)
    conditions: dict[str, Any]  # {op, attr?, value?, children?}
    value: Any
    rollout_percentage: int = Field(default=100, ge=0, le=100)


class RuleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    priority: int | None = Field(default=None, ge=0, le=32000)
    conditions: dict[str, Any] | None = None
    value: Any | None = None
    rollout_percentage: int | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None


class RuleRead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    flag_id: str
    environment: FlagEnvironment
    priority: int
    conditions: dict[str, Any]
    value: Any
    rollout_percentage: int
    is_active: bool
    is_test: bool
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _ts(cls, v: object) -> object:
        if isinstance(v, datetime):
            return v.isoformat()
        return v

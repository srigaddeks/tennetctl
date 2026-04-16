"""featureflags.overrides — Pydantic v2 API models."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator

FlagEnvironment = Literal["dev", "staging", "prod", "test"]
OverrideEntityType = Literal["org", "workspace", "user", "role", "group", "application"]


class OverrideCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    flag_id: str
    environment: FlagEnvironment
    entity_type: OverrideEntityType
    entity_id: str
    value: Any
    reason: str | None = None


class OverrideUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: Any | None = None
    reason: str | None = None
    is_active: bool | None = None


class OverrideRead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    flag_id: str
    environment: FlagEnvironment
    entity_type: OverrideEntityType
    entity_id: str
    value: Any
    reason: str | None = None
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

"""featureflags.permissions — Pydantic v2 API models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

FlagPermission = Literal["view", "toggle", "write", "admin"]


class RoleFlagPermissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role_id: str
    flag_id: str
    permission: FlagPermission


class RoleFlagPermissionRead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    role_id: str
    flag_id: str
    permission: FlagPermission
    permission_rank: int
    created_by: str
    created_at: str

    @field_validator("created_at", mode="before")
    @classmethod
    def _ts(cls, v: object) -> object:
        if isinstance(v, datetime):
            return v.isoformat()
        return v

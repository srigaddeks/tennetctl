"""
iam.memberships — Pydantic v2 API models for user-org and user-workspace lnk rows.

Lnk rows are immutable — no PATCH bodies, revoke = DELETE by id.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


def _coerce_timestamp(v: object) -> object:
    if isinstance(v, datetime):
        return v.isoformat()
    return v


class OrgMembershipCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    org_id: str


class OrgMembershipRead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    org_id: str
    created_by: str
    created_at: str

    @field_validator("created_at", mode="before")
    @classmethod
    def _ts(cls, v: object) -> object:
        return _coerce_timestamp(v)


class WorkspaceMembershipCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    workspace_id: str


class WorkspaceMembershipRead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    workspace_id: str
    org_id: str
    created_by: str
    created_at: str

    @field_validator("created_at", mode="before")
    @classmethod
    def _ts(cls, v: object) -> object:
        return _coerce_timestamp(v)

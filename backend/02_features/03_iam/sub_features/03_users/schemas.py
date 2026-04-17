"""
iam.users — Pydantic v2 API models.

account_type is accepted as a code (string) on create; the service resolves to
account_type_id via dim_account_types. account_type is frozen on PATCH (changing
auth type is a migration, not a casual update).

Status transitions (via PATCH `status` field):
  "active"   → reactivate (or no-op if already active)
  "inactive" → deactivate + revoke all sessions
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _validate_email(v: str) -> str:
    if not _EMAIL_RE.match(v):
        raise ValueError(f"email {v!r} is not a valid email address")
    return v


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_type: str  # code, e.g. "email_password"
    email: str
    display_name: str
    avatar_url: str | None = None

    @field_validator("email")
    @classmethod
    def _email_shape(cls, v: str) -> str:
        return _validate_email(v)


class UserUpdate(BaseModel):
    """PATCH body — only provided fields change. account_type is frozen.

    Use `status` to activate/deactivate. Setting `status` overrides any
    `is_active` value sent in the same request (deprecated field kept for
    backward compatibility).
    """
    model_config = ConfigDict(extra="forbid")

    email: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    # Deprecated — use `status` instead. Kept for backward compat.
    is_active: bool | None = None
    # Preferred status transition field.
    status: Literal["active", "inactive"] | None = None

    @field_validator("email")
    @classmethod
    def _email_shape(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _validate_email(v)


class UserRead(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    account_type: str
    email: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    is_active: bool
    is_test: bool
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _coerce_timestamp(cls, v: object) -> object:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class UserListResponse(BaseModel):
    items: list[UserRead]
    total: int

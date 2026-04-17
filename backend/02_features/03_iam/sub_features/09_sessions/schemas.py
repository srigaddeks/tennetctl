"""
iam.sessions — Pydantic v2 API models.

The read shape mirrors v_sessions (carries derived is_valid). Users only see
their own sessions — no cross-user listing in v1.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SessionRead(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str
    org_id: str | None = None
    workspace_id: str | None = None
    expires_at: str
    revoked_at: str | None = None
    is_valid: bool
    is_active: bool
    created_at: str
    updated_at: str

    @field_validator("expires_at", "revoked_at", "created_at", "updated_at", mode="before")
    @classmethod
    def _coerce_ts(cls, v: object) -> object:
        if v is None:
            return v
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class SessionPatchBody(BaseModel):
    """PATCH body. Today only `extend=true` is supported — pushes expires_at out by
    the default TTL. Idempotent: extending an already-fresh session is a no-op."""
    model_config = ConfigDict(extra="forbid")

    extend: bool = Field(default=False)

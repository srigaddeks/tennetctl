"""Pydantic schemas for iam.api_keys."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=128)
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None


class ApiKeyRow(BaseModel):
    """Sanitized key row — secret_hash never leaves the server."""
    id: str
    org_id: str
    user_id: str
    key_id: str
    label: str
    scopes: list[str]
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    is_active: bool
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class ApiKeyCreatedResponse(ApiKeyRow):
    """One-time response on creation. `token` appears here once and NEVER again."""
    token: str

"""Pydantic schemas for notify.smtp_configs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SmtpConfigCreate(BaseModel):
    org_id: str
    key: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9_-]+$")
    label: str = Field(..., min_length=1, max_length=128)
    host: str = Field(..., min_length=1)
    port: int = Field(default=587, ge=1, le=65535)
    tls: bool = True
    username: str = Field(..., min_length=1)
    auth_vault_key: str = Field(..., min_length=1, description="Vault secret key holding SMTP password")


class SmtpConfigUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=128)
    host: str | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    tls: bool | None = None
    username: str | None = None
    auth_vault_key: str | None = None
    is_active: bool | None = None


class SmtpConfigRow(BaseModel):
    id: str
    org_id: str
    key: str
    label: str
    host: str
    port: int
    tls: bool
    username: str
    auth_vault_key: str
    is_active: bool
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime

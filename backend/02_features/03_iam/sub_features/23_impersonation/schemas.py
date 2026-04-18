"""iam.impersonation — Pydantic schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class StartImpersonationBody(BaseModel):
    target_user_id: str


class ImpersonationRow(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    session_id: str
    impersonator_user_id: str
    impersonated_user_id: str
    org_id: str
    ended_at: Any = None
    created_at: Any = None


class ImpersonationStatus(BaseModel):
    active: bool
    impersonation_id: str | None = None
    impersonated_user_id: str | None = None
    impersonated_display_name: str | None = None
    impersonated_email: str | None = None
    session_expires_at: Any = None

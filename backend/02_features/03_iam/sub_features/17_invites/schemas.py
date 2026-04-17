"""Pydantic schemas for iam.invites."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr


class InviteCreateBody(BaseModel):
    email: EmailStr
    role_id: str | None = None


class AcceptInviteBody(BaseModel):
    token: str
    password: str
    display_name: str


class InviteRead(BaseModel):
    id: str
    org_id: str
    email: str
    invited_by: str
    inviter_email: str | None = None
    inviter_display_name: str | None = None
    role_id: str | None = None
    status: int
    expires_at: str
    accepted_at: str | None = None
    created_at: str
    updated_at: str

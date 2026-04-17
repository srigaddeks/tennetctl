"""Pydantic schemas for iam.magic_link."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class MagicLinkRequest(BaseModel):
    email: EmailStr
    redirect_url: str = Field(
        default="/",
        description="URL to redirect to after successful authentication",
    )


class MagicLinkConsume(BaseModel):
    token: str = Field(..., description="Raw magic-link token from the email URL")


class MagicLinkRequestResponse(BaseModel):
    sent: bool = True
    message: str = "If that email is registered, a sign-in link is on its way."

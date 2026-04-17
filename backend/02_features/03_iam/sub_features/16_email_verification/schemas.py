"""Pydantic schemas for iam.email_verification."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SendVerificationRequest(BaseModel):
    email: str = Field(..., description="Email address to send the verification link to.")


class ConsumeVerificationRequest(BaseModel):
    token: str = Field(..., description="Raw verification token from the email URL.")

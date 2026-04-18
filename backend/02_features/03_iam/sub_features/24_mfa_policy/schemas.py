"""iam.mfa_policy — Pydantic schemas."""

from __future__ import annotations

from pydantic import BaseModel


class MfaPolicyUpdate(BaseModel):
    required: bool


class MfaPolicyStatus(BaseModel):
    org_id: str
    required: bool
    totp_enrolled: bool  # for the calling user

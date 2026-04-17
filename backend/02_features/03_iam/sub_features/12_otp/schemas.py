"""Pydantic schemas for iam.otp (email OTP + TOTP)."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr


class OtpRequest(BaseModel):
    email: EmailStr


class OtpVerify(BaseModel):
    email: EmailStr
    code: str


class TotpSetupRequest(BaseModel):
    device_name: str = "Authenticator"


class TotpSetupResponse(BaseModel):
    credential_id: str
    otpauth_uri: str
    device_name: str


class TotpVerify(BaseModel):
    credential_id: str
    code: str


class TotpCredentialRow(BaseModel):
    id: str
    user_id: str
    device_name: str
    is_active: bool
    last_used_at: str | None
    created_at: str

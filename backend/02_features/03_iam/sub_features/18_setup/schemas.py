"""iam.setup — Pydantic v2 schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator


class SetupStatusResponse(BaseModel):
    initialized: bool
    user_count: int
    setup_required: bool


class InitialAdminBody(BaseModel):
    email: EmailStr
    password: str
    display_name: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v

    @field_validator("display_name")
    @classmethod
    def display_name_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("display_name must not be blank")
        return v.strip()


class InitialAdminResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    totp_credential_id: str
    otpauth_uri: str
    backup_codes: list[str]
    session_token: str
    session: dict

"""Pydantic schemas for iam.passkeys (WebAuthn)."""

from __future__ import annotations

from pydantic import BaseModel


class PasskeyRegisterBeginRequest(BaseModel):
    device_name: str = "Passkey"


class PasskeyRegisterBeginResponse(BaseModel):
    challenge_id: str
    options_json: str


class PasskeyRegisterCompleteRequest(BaseModel):
    challenge_id: str
    credential_json: str  # JSON string from navigator.credentials.create()


class PasskeyAuthBeginRequest(BaseModel):
    email: str


class PasskeyAuthBeginResponse(BaseModel):
    challenge_id: str
    options_json: str


class PasskeyAuthCompleteRequest(BaseModel):
    challenge_id: str
    credential_json: str  # JSON string from navigator.credentials.get()


class PasskeyCredentialRow(BaseModel):
    id: str
    user_id: str
    device_name: str
    aaguid: str
    sign_count: int
    last_used_at: str | None
    created_at: str

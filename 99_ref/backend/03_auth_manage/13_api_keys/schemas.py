from __future__ import annotations

from pydantic import BaseModel, Field


class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    scopes: list[str] | None = None
    expires_in_days: int | None = Field(None, ge=1, le=365)


class RevokeApiKeyRequest(BaseModel):
    reason: str | None = Field(None, max_length=500)


class ApiKeyCreatedResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    api_key: str
    scopes: list[str] | None
    expires_at: str | None
    created_at: str


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    status: str
    scopes: list[str] | None
    expires_at: str | None
    last_used_at: str | None
    last_used_ip: str | None
    revoked_at: str | None
    revoke_reason: str | None = None
    created_at: str


class ApiKeyListResponse(BaseModel):
    items: list[ApiKeyResponse]
    total: int

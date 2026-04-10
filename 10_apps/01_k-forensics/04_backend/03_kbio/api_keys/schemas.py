"""kbio API key schemas.

Pydantic models for API key CRUD operations.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateApiKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    org_id: str
    workspace_id: str
    permissions: dict[str, Any] = Field(default_factory=dict)
    rate_limit: str = ""
    expires_at: str = ""


class UpdateApiKeyRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    rate_limit: str | None = None
    permissions: dict[str, Any] | None = None


class ApiKeyResponse(BaseModel):
    id: str
    org_id: str
    workspace_id: str
    key_prefix: str
    status: str
    name: str | None = None
    description: str | None = None
    last_used_at: str | None = None
    rate_limit: str | None = None
    permissions: dict[str, Any] | None = None
    expires_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ApiKeyCreatedResponse(BaseModel):
    """Returned only on creation — includes the raw key (shown once)."""
    id: str
    raw_key: str
    key_prefix: str
    name: str

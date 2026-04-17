"""iam.oidc_sso — Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class OidcProviderCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=64)
    issuer: str = Field(..., description="OIDC discovery base URL e.g. https://accounts.google.com")
    client_id: str = Field(..., min_length=1)
    client_secret_vault_key: str = Field(..., description="Vault key referencing the client secret")
    scopes: str = Field(default="openid email profile")
    claim_mapping: dict[str, str] = Field(
        default={"email": "email", "name": "name", "sub": "sub"},
    )


class OidcProviderRow(BaseModel):
    id: UUID
    org_id: UUID
    slug: str
    issuer: str
    client_id: str
    client_secret_vault_key: str
    scopes: str
    claim_mapping: dict[str, str]
    enabled: bool
    created_at: datetime
    org_slug: str | None = None

    model_config = {"from_attributes": True}

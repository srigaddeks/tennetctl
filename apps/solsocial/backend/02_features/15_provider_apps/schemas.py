"""Schemas for workspace-level BYO provider apps."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProviderCode = Literal["linkedin", "twitter", "instagram"]


class WorkspaceAppUpsert(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_code: ProviderCode
    client_id: str = Field(min_length=1, max_length=500)
    client_secret: str = Field(min_length=1, max_length=500)
    redirect_uri_hint: str | None = None
    notes: str | None = Field(default=None, max_length=2000)


class WorkspaceAppOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    workspace_id: str
    org_id: str
    provider_code: ProviderCode
    client_id: str               # safe — client_id is not a secret
    has_secret: bool             # never expose the secret
    redirect_uri_hint: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

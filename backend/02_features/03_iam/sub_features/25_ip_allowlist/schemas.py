"""iam.ip_allowlist — Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class IpAllowlistEntry(BaseModel):
    id: str
    org_id: str
    cidr: str
    label: str
    created_by: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class IpAllowlistCreate(BaseModel):
    cidr: str
    label: str = ""

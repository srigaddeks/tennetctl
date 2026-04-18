"""iam.siem_export — Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SiemDestination(BaseModel):
    id: str
    org_id: str
    kind: str
    label: str
    config_jsonb: dict
    is_active: bool
    last_cursor: int
    last_exported_at: datetime | None
    failure_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SiemDestinationCreate(BaseModel):
    kind: str
    label: str = ""
    config_jsonb: dict = {}
    credentials_vault_key: str | None = None


class SiemDestinationUpdate(BaseModel):
    label: str | None = None
    config_jsonb: dict | None = None
    is_active: bool | None = None

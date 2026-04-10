"""kprotect signal_selections schemas -- Pydantic v2."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SignalSelectionData(BaseModel):
    id: str
    org_id: str
    signal_code: str
    config_overrides: dict[str, Any] | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SignalSelectionListData(BaseModel):
    items: list[SignalSelectionData]
    total: int
    limit: int
    offset: int


class CreateSignalSelectionRequest(BaseModel):
    org_id: str
    signal_code: str
    config_overrides: dict[str, Any] | None = None
    notes: str | None = None


class PatchSignalSelectionRequest(BaseModel):
    config_overrides: dict[str, Any] | None = None
    notes: str | None = None
    is_active: bool | None = None


class BulkCreateSignalSelectionsRequest(BaseModel):
    org_id: str
    signal_codes: list[str]
    config_overrides: dict[str, str | dict[str, Any]] | None = None

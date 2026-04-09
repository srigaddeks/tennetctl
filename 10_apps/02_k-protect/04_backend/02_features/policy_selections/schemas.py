"""kprotect policy_selections schemas — Pydantic v2."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PolicySelectionData(BaseModel):
    id: str
    org_id: str
    predefined_policy_code: str
    policy_category: str | None
    policy_name: str | None
    priority: int
    config_overrides: dict[str, Any] | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PolicySelectionListData(BaseModel):
    items: list[PolicySelectionData]
    total: int
    limit: int
    offset: int


class CreatePolicySelectionRequest(BaseModel):
    org_id: str
    predefined_policy_code: str
    # policy_category and policy_name are copied from kbio by the caller
    policy_category: str
    policy_name: str
    priority: int = 100
    config_overrides: dict[str, Any] | None = None
    notes: str | None = None


class PatchPolicySelectionRequest(BaseModel):
    priority: int | None = None
    config_overrides: dict[str, Any] | None = None
    notes: str | None = None
    is_active: bool | None = None

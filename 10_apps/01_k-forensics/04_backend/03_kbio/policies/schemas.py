"""kbio policies schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PolicyRule(BaseModel):
    field: str          # dot-path: "behavioral_drift", "device.is_new"
    op: str             # ==, !=, >, <, >=, <=, IN, NOT_IN, EXISTS, NOT_EXISTS
    value: Any          # threshold or comparison value
    config_key: str | None = None  # optional: use org config override instead of hardcoded value


class PolicyConditions(BaseModel):
    operator: str = "AND"  # AND, OR
    rules: list[PolicyRule] = Field(default_factory=list)
    action: str = "allow"  # allow, monitor, challenge, block, flag, throttle
    reason_template: str = ""


class PredefinedPolicyData(BaseModel):
    id: str
    code: str
    name: str
    description: str
    category: str
    default_action: str
    severity: int
    conditions: dict[str, Any]
    default_config: dict[str, Any]
    tags: str
    version: str
    is_active: bool
    created_at: str


class PredefinedPolicyListData(BaseModel):
    items: list[PredefinedPolicyData]
    total: int
    limit: int
    offset: int

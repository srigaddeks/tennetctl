"""
iam.roles — Pydantic v2 API models.

Roles are either global (org_id NULL) or org-scoped. Role 'code' is the stable
identifier; unique per (org_id, code) — NULL org_id group by itself.
"""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{1,62}$")


def _validate_code(v: str) -> str:
    if not _CODE_RE.match(v):
        raise ValueError(
            f"code {v!r} must match ^[a-z][a-z0-9_]{{1,62}}$ (lowercase snake_case)"
        )
    return v


class RoleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    org_id: str | None = None  # None = global role
    role_type: str  # 'system' | 'custom'
    code: str
    label: str
    description: str | None = None

    @field_validator("code")
    @classmethod
    def _c(cls, v: str) -> str:
        return _validate_code(v)


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # org_id + role_type + code frozen after create
    label: str | None = None
    description: str | None = None
    is_active: bool | None = None


class RoleRead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    org_id: str | None
    role_type: str
    code: str | None = None
    label: str | None = None
    description: str | None = None
    is_active: bool
    is_test: bool
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _ts(cls, v: object) -> object:
        if isinstance(v, datetime):
            return v.isoformat()
        return v

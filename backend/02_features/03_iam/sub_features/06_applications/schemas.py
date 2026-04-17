"""iam.applications — Pydantic v2 API models."""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{1,62}$")


def _validate_code(v: str) -> str:
    if not _CODE_RE.match(v):
        raise ValueError(f"code {v!r} must match ^[a-z][a-z0-9_]{{1,62}}$")
    return v


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    org_id: str
    code: str
    label: str
    description: str | None = None

    @field_validator("code")
    @classmethod
    def _c(cls, v: str) -> str:
        return _validate_code(v)


class ApplicationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str | None = None
    description: str | None = None
    is_active: bool | None = None
    scope_ids: list[int] | None = None


class ApplicationRead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    org_id: str
    code: str | None = None
    label: str | None = None
    description: str | None = None
    is_active: bool
    is_test: bool
    scope_ids: list[int] = []
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

"""Pydantic schemas for product_ops.cohorts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,127}$")

CohortKind = Literal["dynamic", "static"]


class CreateCohortBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str = Field(min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=2048)
    workspace_id: str | None = None
    kind: CohortKind = "dynamic"
    definition: dict[str, Any] = Field(default_factory=dict)
    # For static cohorts: optional initial visitor_id list
    visitor_ids: list[str] | None = None

    @field_validator("slug")
    @classmethod
    def _slug_shape(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError("slug must be lowercase, [a-z0-9][a-z0-9_-]{1,127}")
        return v


class UpdateCohortBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    definition: dict[str, Any] | None = None
    is_active: bool | None = None
    deleted_at: datetime | None = None


class AddMembersBody(BaseModel):
    """Static cohorts only — bulk add visitor_ids."""
    model_config = ConfigDict(extra="forbid")
    visitor_ids: list[str] = Field(min_length=1, max_length=10_000)


class RefreshCohortResponse(BaseModel):
    cohort_id: str
    members_added: int
    members_removed: int
    final_count: int
    duration_ms: int


class CohortOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    slug: str
    name: str
    description: str | None
    org_id: str
    workspace_id: str
    kind: CohortKind
    definition: dict[str, Any]
    last_computed_at: datetime | None
    member_count: int
    is_active: bool
    is_deleted: bool
    deleted_at: datetime | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_refresh_duration_ms: int | None = None
    refresh_count: int | None = None

"""
iam.orgs — Pydantic v2 API models.

OrgCreate / OrgUpdate / OrgRead / OrgListResponse drive the 5-endpoint surface.
Slug validator enforces URL-safe identifiers matching the DB uniqueness contract.
"""

from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{1,62}$")


def _validate_slug(v: str) -> str:
    if not _SLUG_RE.match(v):
        raise ValueError(
            f"slug {v!r} must match ^[a-z][a-z0-9-]{{1,62}}$ "
            f"(lowercase, starts with letter, hyphens allowed)"
        )
    return v


class OrgCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    display_name: str

    @field_validator("slug")
    @classmethod
    def _slug_shape(cls, v: str) -> str:
        return _validate_slug(v)


class OrgUpdate(BaseModel):
    """PATCH body — only provided fields change."""
    model_config = ConfigDict(extra="forbid")

    slug: str | None = None
    display_name: str | None = None

    @field_validator("slug")
    @classmethod
    def _slug_shape(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _validate_slug(v)


class OrgRead(BaseModel):
    """Flat shape returned to API callers. Mirrors v_orgs (minus deleted_at)."""
    model_config = ConfigDict(extra="ignore")

    id: str
    slug: str
    display_name: str | None = None
    is_active: bool
    is_test: bool
    created_by: str
    updated_by: str
    created_at: str
    updated_at: str

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _coerce_timestamp(cls, v: object) -> object:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class OrgListResponse(BaseModel):
    items: list[OrgRead]
    total: int

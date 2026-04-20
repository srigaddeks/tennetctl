"""Pydantic schemas for product_ops.destinations."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,127}$")

DestinationKind = Literal["webhook", "slack", "custom"]
DeliveryStatus = Literal["pending", "success", "failure", "timeout", "rejected_filter"]


class CreateDestinationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str = Field(min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=2048)
    workspace_id: str | None = None
    kind: DestinationKind
    url: str = Field(min_length=1, max_length=2048)
    secret: str | None = Field(default=None, max_length=1024)
    headers: dict[str, str] = Field(default_factory=dict)
    filter_rule: dict[str, Any] = Field(default_factory=dict)
    retry_policy: dict[str, Any] = Field(default_factory=lambda: {"max_attempts": 1, "backoff_ms": 1000})

    @field_validator("slug")
    @classmethod
    def _slug_shape(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError("slug must be lowercase, [a-z0-9][a-z0-9_-]{1,127}")
        return v


class UpdateDestinationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    url: str | None = None
    secret: str | None = None
    headers: dict[str, str] | None = None
    filter_rule: dict[str, Any] | None = None
    retry_policy: dict[str, Any] | None = None
    is_active: bool | None = None
    deleted_at: datetime | None = None


class TestDestinationBody(BaseModel):
    """Send a synthetic event to validate the destination wiring."""
    model_config = ConfigDict(extra="forbid")
    sample_event: dict[str, Any] | None = None


class DestinationOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    slug: str
    name: str
    description: str | None
    org_id: str
    workspace_id: str
    kind: DestinationKind
    url: str
    has_secret: bool
    headers: dict[str, Any]
    filter_rule: dict[str, Any]
    retry_policy: dict[str, Any]
    is_active: bool
    is_deleted: bool
    deleted_at: datetime | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    delivery_count_30d: int = 0
    success_count_30d: int = 0
    failure_count_30d: int = 0

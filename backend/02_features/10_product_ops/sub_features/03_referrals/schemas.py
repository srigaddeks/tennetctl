"""Pydantic schemas for product_ops.referrals."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_CODE_RE = re.compile(r"^[a-zA-Z0-9_-]{3,64}$")


class CreateReferralCodeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=3, max_length=64)
    referrer_user_id: str
    workspace_id: str | None = None
    reward_config: dict[str, Any] = Field(default_factory=dict)

    @field_validator("code")
    @classmethod
    def _code_shape(cls, v: str) -> str:
        if not _CODE_RE.match(v):
            raise ValueError("code must match [A-Za-z0-9_-]{3,64}")
        return v


class AttachReferralBody(BaseModel):
    """Browser-facing endpoint when a visitor lands with ?ref=<code>."""
    model_config = ConfigDict(extra="forbid")

    code: str
    workspace_id: str
    anonymous_id: str
    landing_url: str | None = None


class RecordConversionBody(BaseModel):
    """Backend-facing endpoint when an action resolves a referral (signup/purchase)."""
    model_config = ConfigDict(extra="forbid")

    referral_code_id: str | None = None
    code: str | None = None  # alternative lookup
    visitor_id: str | None = None
    converted_user_id: str | None = None
    workspace_id: str
    conversion_kind: str = Field(min_length=1, max_length=64)
    conversion_value_cents: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None


class ReferralCodeOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    code: str
    referrer_user_id: str
    org_id: str
    workspace_id: str
    reward_config: dict[str, Any]
    is_active: bool
    is_deleted: bool
    deleted_at: datetime | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    conversion_count: int
    conversion_value_cents_total: int

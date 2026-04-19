"""Pydantic schemas for product_ops.partners."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")

CodeKind = Literal["referral", "promo"]
PayoutStatus = Literal["pending", "paid", "failed", "cancelled"]


class CreatePartnerBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    display_name: str = Field(min_length=1, max_length=256)
    contact_email: EmailStr
    workspace_id: str | None = None
    user_id: str | None = None
    tier_id: int = 1  # default to "standard"

    @field_validator("slug")
    @classmethod
    def _slug_shape(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError("slug must be lowercase, [a-z0-9][a-z0-9_-]{1,63}")
        return v


class UpdatePartnerBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = None
    contact_email: EmailStr | None = None
    user_id: str | None = None
    tier_id: int | None = None
    is_active: bool | None = None
    deleted_at: datetime | None = None


class LinkCodeBody(BaseModel):
    """Attach a referral or promo code to a partner."""
    model_config = ConfigDict(extra="forbid")

    code_kind: CodeKind
    referral_code_id: str | None = None
    promo_code_id: str | None = None
    payout_bp_override: int | None = Field(default=None, ge=0, le=10_000)


class CreatePayoutBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period_start: datetime
    period_end: datetime
    amount_cents: int = Field(ge=0)
    currency: str = "USD"
    status: PayoutStatus = "pending"
    paid_at: datetime | None = None
    external_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PartnerOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    slug: str
    display_name: str
    contact_email: str
    org_id: str
    workspace_id: str
    user_id: str | None
    tier_id: int
    tier_code: str
    tier_label: str
    default_payout_bp: int
    is_active: bool
    is_deleted: bool
    deleted_at: datetime | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    code_count: int
    conversion_count: int
    conversion_value_cents_total: int
    payout_paid_cents: int
    payout_pending_cents: int

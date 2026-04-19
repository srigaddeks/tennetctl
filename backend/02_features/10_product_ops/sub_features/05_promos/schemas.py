"""Pydantic schemas for product_ops.promos."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_CODE_RE = re.compile(r"^[a-zA-Z0-9_-]{2,64}$")

# RedemptionKind is intentionally a free string at the schema layer —
# dim_promotion_kinds is operator-extensible. Service layer validates against
# the dim FK at create time; Pydantic only enforces the surface shape.
RedemptionKind = str
PromoStatus = Literal["scheduled", "active", "expired", "inactive", "exhausted"]
RedemptionOutcome = Literal[
    "redeemed",
    "rejected_max_uses",
    "rejected_per_visitor",
    "rejected_expired",
    "rejected_inactive",
    "rejected_eligibility",
    "rejected_unknown_code",
]


class CreatePromoCodeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=2, max_length=64)
    workspace_id: str | None = None
    redemption_kind: RedemptionKind
    redemption_config: dict[str, Any] = Field(default_factory=dict)
    description: str | None = Field(default=None, max_length=1024)
    max_total_uses: int | None = Field(default=None, ge=1)
    max_uses_per_visitor: int = Field(default=1, ge=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    eligibility: dict[str, Any] = Field(default_factory=dict)

    @field_validator("code")
    @classmethod
    def _code_shape(cls, v: str) -> str:
        if not _CODE_RE.match(v):
            raise ValueError("code must match [A-Za-z0-9_-]{2,64}")
        return v


class UpdatePromoCodeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str | None = None
    max_total_uses: int | None = None
    max_uses_per_visitor: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    eligibility: dict[str, Any] | None = None
    is_active: bool | None = None
    deleted_at: datetime | None = None


class RedeemPromoBody(BaseModel):
    """Public-facing redemption attempt. Returns outcome + (if redeemed) reward shape."""
    model_config = ConfigDict(extra="forbid")

    code: str
    workspace_id: str
    visitor_id: str | None = None
    anonymous_id: str | None = None
    redeemer_user_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RedeemPromoResponse(BaseModel):
    outcome: RedemptionOutcome
    redemption_id: str | None = None
    promo_code_id: str | None = None
    redemption_kind: RedemptionKind | None = None
    redemption_config: dict[str, Any] | None = None
    rejection_reason: str | None = None


class PromoCodeOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    code: str
    org_id: str
    workspace_id: str
    redemption_kind: RedemptionKind
    redemption_config: dict[str, Any]
    description: str | None
    max_total_uses: int | None
    max_uses_per_visitor: int
    starts_at: datetime | None
    ends_at: datetime | None
    eligibility: dict[str, Any]
    is_active: bool
    is_deleted: bool
    deleted_at: datetime | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    redemption_count: int
    rejection_count: int
    status: PromoStatus

"""Pydantic schemas for product_ops.campaigns."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,127}$")

CampaignStatus = Literal["scheduled", "active", "ended", "inactive"]
CampaignDecision = Literal["weighted_pick", "eligibility_miss", "no_active_promos"]


class CreateCampaignBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str = Field(min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=2048)
    workspace_id: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    audience_rule: dict[str, Any] = Field(default_factory=dict)
    goals: dict[str, Any] = Field(default_factory=dict)

    @field_validator("slug")
    @classmethod
    def _slug_shape(cls, v: str) -> str:
        if not _SLUG_RE.match(v):
            raise ValueError("slug must be lowercase, [a-z0-9][a-z0-9_-]{1,127}")
        return v


class UpdateCampaignBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    audience_rule: dict[str, Any] | None = None
    goals: dict[str, Any] | None = None
    is_active: bool | None = None
    deleted_at: datetime | None = None


class LinkPromoBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    promo_code_id: str
    weight: int = Field(default=1, ge=1)
    audience_rule_override: dict[str, Any] | None = None


class PickPromoBody(BaseModel):
    """Public endpoint: given a campaign + visitor context, return which promo
    (if any) the visitor should see. Logs an exposure row regardless."""
    model_config = ConfigDict(extra="forbid")

    campaign_slug: str | None = None
    campaign_id: str | None = None
    workspace_id: str
    visitor_id: str | None = None
    anonymous_id: str | None = None
    eligibility_context: dict[str, Any] = Field(default_factory=dict)


class PickPromoResponse(BaseModel):
    decision: CampaignDecision
    campaign_id: str
    promo_code_id: str | None
    promo_code: str | None
    redemption_kind: str | None
    redemption_config: dict[str, Any] | None
    rejection_reason: str | None = None


class CampaignOut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    slug: str
    name: str
    description: str | None
    org_id: str
    workspace_id: str
    starts_at: datetime | None
    ends_at: datetime | None
    audience_rule: dict[str, Any]
    goals: dict[str, Any]
    is_active: bool
    is_deleted: bool
    deleted_at: datetime | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    promo_count: int
    exposure_count: int
    redemption_count: int
    status: CampaignStatus

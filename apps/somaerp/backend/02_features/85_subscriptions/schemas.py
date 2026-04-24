"""Pydantic v2 schemas for subscription frequencies, plans, plan items,
subscriptions, and events."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SubscriptionPlanStatus = Literal["draft", "active", "archived"]
SubscriptionStatus = Literal["active", "paused", "cancelled", "ended"]
SubscriptionEventType = Literal[
    "started", "paused", "resumed", "cancelled", "ended",
    "plan_changed", "frequency_changed",
]


# ── Frequencies (read-only dim) ───────────────────────────────────────────


class SubscriptionFrequencyOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    name: str
    deliveries_per_week: Decimal
    deprecated_at: datetime | None = None


# ── Plans ────────────────────────────────────────────────────────────────


class SubscriptionPlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    description: str | None = None
    frequency_id: int
    price_per_delivery: Decimal | None = Field(default=None, ge=0)
    currency_code: str = Field(min_length=3, max_length=3)
    status: SubscriptionPlanStatus = "active"
    properties: dict[str, Any] = Field(default_factory=dict)


class SubscriptionPlanUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    description: str | None = None
    frequency_id: int | None = None
    price_per_delivery: Decimal | None = Field(default=None, ge=0)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    status: SubscriptionPlanStatus | None = None
    properties: dict[str, Any] | None = None


class SubscriptionPlanOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    name: str
    slug: str
    description: str | None = None
    frequency_id: int
    frequency_code: str | None = None
    frequency_name: str | None = None
    deliveries_per_week: Decimal | None = None
    price_per_delivery: Decimal | None = None
    currency_code: str
    status: SubscriptionPlanStatus
    properties: dict[str, Any] = Field(default_factory=dict)
    item_count: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Plan items ───────────────────────────────────────────────────────────


class SubscriptionPlanItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str
    variant_id: str | None = None
    qty_per_delivery: Decimal = Field(gt=0)
    position: int = 0
    notes: str | None = None


class SubscriptionPlanItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str | None = None
    variant_id: str | None = None
    qty_per_delivery: Decimal | None = Field(default=None, gt=0)
    position: int | None = None
    notes: str | None = None


class SubscriptionPlanItemOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    plan_id: str
    product_id: str
    product_name: str | None = None
    product_slug: str | None = None
    variant_id: str | None = None
    variant_name: str | None = None
    qty_per_delivery: Decimal
    position: int = 0
    notes: str | None = None
    line_price: Decimal | None = None
    currency_code: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Subscriptions ────────────────────────────────────────────────────────


class SubscriptionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: str
    plan_id: str
    service_zone_id: str | None = None
    start_date: date
    end_date: date | None = None
    billing_cycle: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class SubscriptionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service_zone_id: str | None = None
    end_date: date | None = None
    status: SubscriptionStatus | None = None
    paused_from: date | None = None
    paused_to: date | None = None
    reason: str | None = None
    billing_cycle: str | None = None
    properties: dict[str, Any] | None = None


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    customer_id: str
    customer_name: str | None = None
    customer_slug: str | None = None
    plan_id: str
    plan_name: str | None = None
    plan_slug: str | None = None
    frequency_id: int | None = None
    frequency_code: str | None = None
    frequency_name: str | None = None
    price_per_delivery: Decimal | None = None
    service_zone_id: str | None = None
    service_zone_name: str | None = None
    start_date: date
    end_date: date | None = None
    status: SubscriptionStatus
    paused_from: date | None = None
    paused_to: date | None = None
    billing_cycle: str | None = None
    currency_code: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Events ───────────────────────────────────────────────────────────────


class SubscriptionEventOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    subscription_id: str
    event_type: SubscriptionEventType
    from_date: date | None = None
    to_date: date | None = None
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    ts: datetime
    performed_by_user_id: str
    created_at: datetime

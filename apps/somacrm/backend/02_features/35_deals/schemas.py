"""Pydantic v2 schemas for deals."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DealCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=500)
    contact_id: str | None = None
    organization_id: str | None = None
    stage_id: str | None = None
    status_id: int = Field(default=1)
    value: Decimal | None = None
    currency: str = Field(default="INR", max_length=10)
    expected_close_date: date | None = None
    actual_close_date: date | None = None
    probability_pct: int | None = Field(default=None, ge=0, le=100)
    assigned_to: str | None = None
    description: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class DealUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=500)
    contact_id: str | None = None
    organization_id: str | None = None
    stage_id: str | None = None
    status_id: int | None = None
    value: Decimal | None = None
    currency: str | None = Field(default=None, max_length=10)
    expected_close_date: date | None = None
    actual_close_date: date | None = None
    probability_pct: int | None = Field(default=None, ge=0, le=100)
    assigned_to: str | None = None
    description: str | None = None
    properties: dict[str, Any] | None = None


class DealOut(BaseModel):
    """Mirror of v_deals row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    title: str
    contact_id: str | None = None
    organization_id: str | None = None
    contact_name: str | None = None
    organization_name: str | None = None
    stage_id: str | None = None
    stage_name: str | None = None
    stage_color: str | None = None
    stage_order: int | None = None
    status_id: int
    status: str | None = None
    value: Decimal | None = None
    currency: str
    expected_close_date: date | None = None
    actual_close_date: date | None = None
    probability_pct: int | None = None
    assigned_to: str | None = None
    description: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    deleted_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: datetime
    updated_at: datetime

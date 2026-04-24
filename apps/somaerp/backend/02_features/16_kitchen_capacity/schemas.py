"""Pydantic v2 schemas for geography.kitchen_capacity.

Per ADR-003:
- POST creates a new row (with valid_from, optional valid_to).
- PATCH is a CLOSE operation only — sets valid_to on an active row. Capacity
  values are never updated in place; produce a new row with a new valid_from.
"""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CapacityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_line_id: str
    capacity_value: Decimal = Field(gt=0)
    capacity_unit_id: int
    time_window_start: time
    time_window_end: time
    valid_from: date
    valid_to: date | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class CapacityClosePatch(BaseModel):
    """PATCH only supports closing an active row by setting valid_to."""

    model_config = ConfigDict(extra="forbid")
    valid_to: date


class CapacityOut(BaseModel):
    """Mirror of v_kitchen_current_capacity / v_kitchen_capacity_history row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    kitchen_id: str
    kitchen_name: str | None = None
    product_line_id: str
    product_line_name: str | None = None
    capacity_value: Decimal
    capacity_unit_id: int
    capacity_unit_code: str | None = None
    capacity_unit_name: str | None = None
    time_window_start: time
    time_window_end: time
    valid_from: date
    valid_to: date | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


class CapacityListFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_line_id: str | None = None
    valid_on: date | None = None
    include_history: bool = False
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    include_deleted: bool = False

"""Pydantic v2 schemas for equipment + equipment categories + kitchen-equipment links."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

EquipmentStatus = Literal["active", "maintenance", "retired"]


# ── Equipment Categories (read-only) ────────────────────────────────────

class EquipmentCategoryOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    name: str
    deprecated_at: datetime | None = None


# ── Equipment ───────────────────────────────────────────────────────────

class EquipmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: int
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    status: EquipmentStatus = "active"
    purchase_cost: Decimal | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    purchase_date: date | None = None
    expected_lifespan_months: int | None = Field(default=None, ge=0)
    properties: dict[str, Any] = Field(default_factory=dict)


class EquipmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200,
        pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    status: EquipmentStatus | None = None
    purchase_cost: Decimal | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    purchase_date: date | None = None
    expected_lifespan_months: int | None = Field(default=None, ge=0)
    properties: dict[str, Any] | None = None


class EquipmentOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    category_id: int
    category_code: str | None = None
    category_name: str | None = None
    name: str
    slug: str
    status: EquipmentStatus
    purchase_cost: Decimal | None = None
    currency_code: str | None = None
    purchase_date: date | None = None
    expected_lifespan_months: int | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Kitchen <-> Equipment link (IMMUTABLE) ──────────────────────────────

class KitchenEquipmentLinkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    equipment_id: str
    quantity: int = Field(default=1, ge=1)
    notes: str | None = None


class KitchenEquipmentLinkOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    kitchen_id: str
    kitchen_name: str | None = None
    equipment_id: str
    equipment_name: str | None = None
    equipment_slug: str | None = None
    equipment_status: str | None = None
    equipment_category_code: str | None = None
    equipment_category_name: str | None = None
    quantity: int
    notes: str | None = None
    created_at: datetime
    created_by: str

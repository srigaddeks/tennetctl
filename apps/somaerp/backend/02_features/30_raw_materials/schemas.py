"""Pydantic v2 schemas for raw_materials + variants + categories + units (reads)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RawMaterialStatus = Literal["active", "paused", "discontinued"]
RawMaterialVariantStatus = Literal["active", "paused"]


# ── Read-only dim schemas ────────────────────────────────────────────────


class RawMaterialCategoryOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    name: str
    deprecated_at: datetime | None = None


class UnitOfMeasureOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    code: str
    name: str
    dimension: Literal["mass", "volume", "count"]
    base_unit_id: int | None = None
    to_base_factor: Decimal
    deprecated_at: datetime | None = None


# ── Raw materials ────────────────────────────────────────────────────────


class RawMaterialCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: int
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    default_unit_id: int
    default_shelf_life_hours: int | None = Field(default=None, ge=0)
    requires_lot_tracking: bool = True
    target_unit_cost: Decimal | None = None
    currency_code: str = Field(min_length=3, max_length=3)
    status: RawMaterialStatus = "active"
    properties: dict[str, Any] = Field(default_factory=dict)


class RawMaterialUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    default_unit_id: int | None = None
    default_shelf_life_hours: int | None = Field(default=None, ge=0)
    requires_lot_tracking: bool | None = None
    target_unit_cost: Decimal | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    status: RawMaterialStatus | None = None
    properties: dict[str, Any] | None = None


class RawMaterialOut(BaseModel):
    """Mirror of v_raw_materials row."""

    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    category_id: int
    category_code: str | None = None
    category_name: str | None = None
    name: str
    slug: str
    default_unit_id: int
    default_unit_code: str | None = None
    default_unit_name: str | None = None
    default_unit_dimension: Literal["mass", "volume", "count"] | None = None
    default_shelf_life_hours: int | None = None
    requires_lot_tracking: bool
    target_unit_cost: Decimal | None = None
    currency_code: str
    status: RawMaterialStatus
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None


# ── Raw material variants ────────────────────────────────────────────────


class RawMaterialVariantCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$")
    target_unit_cost: Decimal | None = None
    currency_code: str = Field(min_length=3, max_length=3)
    is_default: bool = False
    status: RawMaterialVariantStatus = "active"
    properties: dict[str, Any] = Field(default_factory=dict)


class RawMaterialVariantUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(
        default=None, min_length=1, max_length=200, pattern=r"^[a-z0-9][a-z0-9-]*$",
    )
    target_unit_cost: Decimal | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    is_default: bool | None = None
    status: RawMaterialVariantStatus | None = None
    properties: dict[str, Any] | None = None


class RawMaterialVariantOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    tenant_id: str
    raw_material_id: str
    raw_material_name: str | None = None
    raw_material_slug: str | None = None
    name: str
    slug: str
    target_unit_cost: Decimal | None = None
    currency_code: str
    is_default: bool
    status: RawMaterialVariantStatus
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    deleted_at: datetime | None = None
